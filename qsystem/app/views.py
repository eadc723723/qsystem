from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from .forms import UsernameAuthenticationForm
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
import json
from django.db.models import Q
from django.utils import timezone
from .forms import StaffSignInForm
from .models import Counter, Activity, CounterActivityAssignment, QueueNumber, StaffProfile
from django.db.models import Prefetch

# select activity
def select_activity(request):
    today = timezone.now().date()
    
    # Prefetch related assignments and counters
    activities = Activity.objects.filter(mode='active').prefetch_related(
        Prefetch('counteractivityassignment_set', queryset=CounterActivityAssignment.objects.filter(date=today), to_attr='active_assignments')
    )
    
    context = []
    
    for activity in activities:
        # Check if there are any active assignments
        assignment = activity.active_assignments[0] if activity.active_assignments else None
        
        if assignment:
            counter = assignment.counter
            context.append({
                'activity': activity,
                'counter_name': counter.name,
                'counter_status': counter.status
            })
        else:
            context.append({
                'activity': activity,
                'counter_name': 'N/A',
                'counter_status': 'Offline'
            })
    
    return render(request, 'select_activity.html', {'activities_with_status': context})

# generate queue number
def queue_number(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    today = timezone.now().date()

    # Get the current active assignment for the activity
    assignment = CounterActivityAssignment.objects.filter(
        activity=activity,
        date=today
    ).first()

    if not assignment:
        return HttpResponseBadRequest("No active counter for the selected activity")

    counter = assignment.counter

    # Check the latest queue number for today
    last_queue_number = QueueNumber.objects.filter(activity=activity, date=today).order_by('number').last()

    # Determine the next queue number
    if last_queue_number:
        next_number = last_queue_number.number + 1
    else:
        next_number = 1  # Start from 1 if no numbers have been issued today

    # Create the queue number with the assigned counter
    queue_number = QueueNumber.objects.create(activity=activity, counter=counter, number=next_number, date=today)

    return redirect('queue_number_display', queue_number_id=queue_number.id)


# queue number display
def queue_number_display(request, queue_number_id):
    queue_number = get_object_or_404(QueueNumber, id=queue_number_id)
    return render(request, 'queue_number_display.html', {'queue_number': queue_number})

# staff sign-in
@login_required
def staff_sign_in(request):
    if request.method == 'POST':
        form = StaffSignInForm(request.POST)
        if form.is_valid():
            counter = form.cleaned_data['counter']
            activity = form.cleaned_data['activity']

            # Get or create staff profile
            staff_profile, created = StaffProfile.objects.get_or_create(user=request.user)
            
            # Update the counter status to 'online'
            counter.status = 'online'
            counter.save()

            # Assign the counter to the activity
            CounterActivityAssignment.objects.create(
                counter=counter,
                activity=activity,
                date=timezone.now().date()
            )

            # Update staff profile with the selected counter and current activity
            staff_profile.counter = counter
            staff_profile.current_activity = activity
            staff_profile.save()

            return redirect('staff_dashboard')
    else:
        form = StaffSignInForm()

    return render(request, 'staff_sign_in.html', {'form': form})


# staff sign-out
def sign_out_and_log_out(request):
    staff_profile = get_object_or_404(StaffProfile, user=request.user)

    if staff_profile.counter:
        # Get the assigned counter
        counter = staff_profile.counter

        # Set the counter status to 'offline'
        counter.status = 'offline'
        counter.save()

        # Remove the counter assignment for the current date
        CounterActivityAssignment.objects.filter(
            counter=counter,
            activity=staff_profile.current_activity,
            date=timezone.now().date()
        ).delete()

    # Clear the staff profile fields
    staff_profile.counter = None
    staff_profile.current_activity = None
    staff_profile.save()

    # Log out the user
    logout(request)

    # Redirect to the login page
    return redirect('login')

# staff_dashboard
@login_required(login_url='/login/')
def staff_dashboard(request):
    # Get the staff profile
    staff_profile = get_object_or_404(StaffProfile, user=request.user)
    
    if not staff_profile.counter:
        return redirect('staff_sign_in')  # Redirect if no counter is assigned

    staff_counter = staff_profile.counter

    # Get the current activity assigned to this counter
    current_assignment = get_object_or_404(CounterActivityAssignment, counter=staff_counter, date=timezone.now().date())
    activity = current_assignment.activity
    activity_code = activity.code  # Use the activity's code

    # Filter issued queue numbers for the current activity and counter
    issued_queue_numbers = QueueNumber.objects.filter(
        activity=activity,
        number__gte=activity_code,
        status='issued'  # Only include numbers with status 'issued'
    ).order_by('issued_at')

    # Get the most recent 5 called queue numbers for the current activity and counter
    called_queue_numbers = QueueNumber.objects.filter(
        activity=activity,
        number__gte=activity_code,
        status='called'  # Include only numbers with status 'called'
    ).order_by('-called_at')[:5]

    if request.method == 'POST':
        action = request.POST.get('action')
        queue_number_id = request.POST.get('queue_number_id')
        queue_number = get_object_or_404(QueueNumber, id=queue_number_id)

        if action == 'call':
            queue_number.status = 'called'
            queue_number.called_at = timezone.now()
        elif action == 'serve':
            queue_number.status = 'served'
            queue_number.called_at = None
        elif action == 'cancel':
            queue_number.status = 'cancelled'
            queue_number.called_at = None
        queue_number.save()

        return redirect('staff_dashboard')

    return render(request, 'staff_dashboard.html', {
        'activity': activity,
        'issued_queue_numbers': issued_queue_numbers,
        'called_queue_numbers': called_queue_numbers,
        'counter': staff_counter,
    })


#re-call numbers
def reinforce_called_numbers(request):
    # Get the staff profile and current counter
    staff_profile = get_object_or_404(StaffProfile, user=request.user)

    if not staff_profile.counter:
        return JsonResponse({'error': 'No counter assigned to this staff.'}, status=400)  # Handle the case where no counter is assigned

    staff_counter = staff_profile.counter

    # Get the current activity assigned to this counter
    current_assignment = get_object_or_404(CounterActivityAssignment, counter=staff_counter, date=timezone.now().date())
    activity = current_assignment.activity

    # Retrieve the issued queue numbers for the current activity
    issued_queue_numbers = QueueNumber.objects.filter(
        activity=activity,
        status='issued'
    ).order_by('issued_at')

    # Retrieve the most recent 5 called queue numbers for the current activity
    called_queue_numbers = QueueNumber.objects.filter(
        activity=activity,
        status='called'
    ).order_by('-called_at')[:5]

    # Prepare the result data
    result = {
        'issued_queue_numbers': list(issued_queue_numbers.values('id', 'number', 'status')),
        'called_queue_numbers': list(called_queue_numbers.values('id', 'number', 'status')),
    }

    return JsonResponse(result)


# retreve queue number to show on staff dasboard
def get_queue_numbers(request):
    activity = request.user.staffprofile.current_activity
    queue_numbers = QueueNumber.objects.filter(activity=activity, status='issued').values('id', 'number', 'status')
    return JsonResponse(list(queue_numbers), safe=False)

#update_queue_status
@login_required
@csrf_exempt
def update_queue_status(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            action = data.get("action")
            queue_number_id = data.get("queue_number_id")

            queue_number = QueueNumber.objects.get(id=queue_number_id)

            if action == "call":
                if queue_number.status == "issued":
                    queue_number.status = "called"
                    queue_number.called_at = timezone.now()
                    # Reset the is_recalled flag after fetching the queue numbers
                    QueueNumber.objects.filter(is_recalled=True).update(is_recalled=False)
            elif action == "serve":
                if queue_number.status == "called":
                    queue_number.status = "served"
                    queue_number.called_at = None
            elif action == "cancel":
                if queue_number.status in ["issued", "called"]:
                    queue_number.status = "cancelled"
                    queue_number.called_at = None
            elif action == "recall":
                if queue_number.status == "called":
                    queue_number.is_recalled = True  # Set the recalled flag
                    queue_number.save()  # Save the recall status

                    return JsonResponse({
                        'success': True,
                        'new_status': queue_number.get_status_display()
                    })
            else:
                return HttpResponseBadRequest("Invalid action")

            queue_number.save()

            return JsonResponse({
                'success': True,
                'new_status': queue_number.get_status_display()
            })

        except QueueNumber.DoesNotExist:
            return HttpResponseBadRequest("Queue number does not exist")
        except Exception as e:
            return HttpResponseBadRequest(f"An error occurred: {str(e)}")
    else:
        return HttpResponseBadRequest("Invalid request method")
    

#login
def user_login(request):
    if request.method == 'POST':
        form = UsernameAuthenticationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            user = authenticate(request, username=username)
            if user is not None:
                login(request, user)
                messages.success(request, 'You have been logged in successfully!')
                return redirect('staff_sign_in')  # Redirect to the dashboard or any other page
            else:
                messages.error(request, 'Authentication failed.')
    else:
        form = UsernameAuthenticationForm()

    return render(request, 'login.html', {'form': form})

#display queue
def get_current_queue_info(request):
    today = timezone.localdate()

    queue_numbers = QueueNumber.objects.filter(
        status__in=['called'],
        issued_at__date=today  # Filter by today's date
    ).order_by('-is_recalled', '-called_at')

    # Prepare data to return
    queue_info = []
    for queue in queue_numbers:
        queue_info.append({
            'id': queue.id,
            'number': queue.number,
            'counter': queue.counter.name if queue.counter else "N/A",
            'is_recalled': queue.is_recalled,
            'issued_at': queue.issued_at,
        })

    return JsonResponse({'queue_numbers': queue_info})

#display monitor 
def monitor_display(request):
    now = timezone.now()
    start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    recalled_queue_numbers = QueueNumber.objects.filter(
        Q(is_recalled=True),
        issued_at__gte=start_of_today
    ).order_by('-issued_at')[:4]
    
    other_queue_numbers = QueueNumber.objects.filter(
        Q(is_recalled=False),
        issued_at__gte=start_of_today
    ).order_by('-issued_at')[:4 - len(recalled_queue_numbers)]
    
    latest_queue_numbers = list(recalled_queue_numbers) + list(other_queue_numbers)
    
    indices = list(range(len(latest_queue_numbers)))
    
    return render(request, 'monitor_display.html', {
        'queue_numbers': latest_queue_numbers,
        'indices': indices
    })

#auto sign out if browser close
@csrf_exempt
def ajax_sign_out(request):
    if request.method == 'POST':
        user = request.user
        if user.is_authenticated:
            staff_profile = get_object_or_404(StaffProfile, user=user)
            if staff_profile.counter:
                counter = staff_profile.counter
                
                # Set the counter status to 'offline'
                counter.status = 'offline'
                counter.save()

                # Remove the counter assignment for the current date
                CounterActivityAssignment.objects.filter(
                    counter=counter,
                    activity=staff_profile.current_activity,
                    date=timezone.now().date()
                ).delete()

            # Clear the staff profile fields
            staff_profile.counter = None
            staff_profile.current_activity = None
            staff_profile.save()

            # Log out the user
            logout(request)
            return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'failed'}, status=400)