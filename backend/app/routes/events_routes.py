from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session
from ..config.db import db
from ..models.user import Event, EventRegistration, User
from datetime import datetime

events_bp = Blueprint("events", __name__, url_prefix="/events")

#  current user
def get_current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

@events_bp.route("/")
def list_events():
    user = get_current_user()
    
    
    upcoming_events = Event.query.filter(
        Event.start_date > datetime.utcnow(),
        Event.is_published == True
    ).order_by(Event.start_date).all()
    

    past_events = Event.query.filter(
        Event.start_date <= datetime.utcnow(),
        Event.is_published == True
    ).order_by(Event.start_date.desc()).limit(10).all()
    
    return render_template("events/list.html", 
                         user=user,
                         upcoming_events=upcoming_events,
                         past_events=past_events)

@events_bp.route("/create", methods=['GET', 'POST'])
def create_event():
    user = get_current_user()
    if not user or user.role not in ['alumni', 'admin']:
        flash('You need to be logged in as alumni to create events.', 'error')
        return redirect(url_for('views.login_page'))
    
    if request.method == 'POST':
        try:
          
            title = request.form.get('title')
            description = request.form.get('description')
            event_type = request.form.get('event_type')
            event_mode = request.form.get('event_mode')
            
            
            start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%dT%H:%M')
            end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%dT%H:%M')
            
            location = request.form.get('location')
            online_link = request.form.get('online_link')
            capacity = request.form.get('capacity')
            price = request.form.get('price', 0)
            
           
            if start_date >= end_date:
                flash('End date must be after start date.', 'error')
                return render_template("events/create.html", user=user)
            
            new_event = Event(
                title=title,
                description=description,
                event_type=event_type,
                event_mode=event_mode,
                start_date=start_date,
                end_date=end_date,
                location=location,
                online_link=online_link,
                capacity=int(capacity) if capacity else None,
                price=float(price),
                organizer_id=user.id,
                is_published=True
            )
            
            db.session.add(new_event)
            db.session.commit()
            
            flash('Event created successfully!', 'success')
            return redirect(url_for('events.view_event', event_id=new_event.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating event: {str(e)}', 'error')
            return render_template("events/create.html", user=user)
    
    return render_template("events/create.html", user=user)

@events_bp.route("/<int:event_id>")
def view_event(event_id):
    user = get_current_user()
    event = Event.query.get_or_404(event_id)
    
  
    organizer = User.query.get(event.organizer_id) if event.organizer_id else None
    
    
    is_registered = False
    registration = None
    if user:
        registration = EventRegistration.query.filter_by(
            event_id=event_id, 
            user_id=user.id
        ).first()
        is_registered = registration is not None
    
    
    attendees = EventRegistration.query.filter_by(
        event_id=event_id,
        status='registered'
    ).all()
    
    return render_template("events/view.html", 
                         user=user, 
                         event=event,
                         organizer=organizer,
                         is_registered=is_registered,
                         registration=registration,
                         attendees=attendees)

@events_bp.route("/<int:event_id>/register", methods=['POST'])
def register_event(event_id):
    user = get_current_user()
    if not user:
        flash('Please login to register for events.', 'error')
        return redirect(url_for('views.login_page'))
    
    event = Event.query.get_or_404(event_id)
    
    
    if not event.registration_available:
        flash('Registration is not available for this event.', 'error')
        return redirect(url_for('events.view_event', event_id=event_id))
    
    
    existing = EventRegistration.query.filter_by(
        event_id=event_id,
        user_id=user.id
    ).first()
    
    if existing:
        if existing.status == 'cancelled':
           
            existing.status = 'registered'
            db.session.commit()
            flash('Your registration has been reactivated!', 'success')
        else:
            flash('You are already registered for this event.', 'info')
    else:
        registration = EventRegistration(
            event_id=event_id,
            user_id=user.id,
            payment_amount=event.price,
            payment_status='free' if event.price == 0 else 'pending'
        )
        db.session.add(registration)
        db.session.commit()
        flash('Successfully registered for the event!', 'success')
    
    return redirect(url_for('events.view_event', event_id=event_id))

@events_bp.route("/<int:event_id>/cancel", methods=['POST'])
def cancel_registration(event_id):
    user = get_current_user()
    if not user:
        flash('Please login to cancel registration.', 'error')
        return redirect(url_for('views.login_page'))
    
    registration = EventRegistration.query.filter_by(
        event_id=event_id,
        user_id=user.id
    ).first()
    
    if registration:
        registration.status = 'cancelled'
        db.session.commit()
        flash('Registration cancelled successfully.', 'success')
    else:
        flash('No registration found for this event.', 'error')
    
    return redirect(url_for('events.view_event', event_id=event_id))

@events_bp.route("/my-events")
def my_events():
    user = get_current_user()
    if not user:
        return redirect(url_for('views.login_page'))
    
    if user.role == 'alumni' or user.role == 'admin':
       
        organized_events = Event.query.filter_by(organizer_id=user.id).order_by(Event.start_date.desc()).all()
    else:
        organized_events = []
    
  
    registrations = EventRegistration.query.filter_by(
        user_id=user.id,
        status='registered'
    ).all()
    registered_events = [r.event for r in registrations]
    
    return render_template("events/my_events.html",
                         user=user,
                         organized_events=organized_events,
                         registered_events=registered_events)

@events_bp.route("/<int:event_id>/edit", methods=['GET', 'POST'])
def edit_event(event_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('views.login_page'))
    
    event = Event.query.get_or_404(event_id)
    
 
    if event.organizer_id != user.id and user.role != 'admin':
        flash('You do not have permission to edit this event.', 'error')
        return redirect(url_for('events.view_event', event_id=event_id))
    
    if request.method == 'POST':
        try:
            event.title = request.form.get('title')
            event.description = request.form.get('description')
            event.event_type = request.form.get('event_type')
            event.event_mode = request.form.get('event_mode')
            event.start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%dT%H:%M')
            event.end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%dT%H:%M')
            event.location = request.form.get('location')
            event.online_link = request.form.get('online_link')
            event.capacity = int(request.form.get('capacity')) if request.form.get('capacity') else None
            event.price = float(request.form.get('price', 0))
            
            db.session.commit()
            flash('Event updated successfully!', 'success')
            return redirect(url_for('events.view_event', event_id=event.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating event: {str(e)}', 'error')
    
    return render_template("events/edit.html", user=user, event=event)

@events_bp.route("/<int:event_id>/delete", methods=['POST'])
def delete_event(event_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('views.login_page'))
    
    event = Event.query.get_or_404(event_id)
    
    
    if event.organizer_id != user.id and user.role != 'admin':
        flash('You do not have permission to delete this event.', 'error')
        return redirect(url_for('events.view_event', event_id=event_id))
    
    try:
        db.session.delete(event)
        db.session.commit()
        flash('Event deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting event: {str(e)}', 'error')
    
    return redirect(url_for('events.list_events'))


@events_bp.route("/alumni")
def alumni_events():
    user = get_current_user()
    if not user or user.role != 'alumni':
        return redirect(url_for('views.login_page'))
    
   
    upcoming_events = Event.query.filter(
        Event.start_date > datetime.utcnow(),
        Event.is_published == True
    ).order_by(Event.start_date).limit(6).all()
    
   
    my_events = Event.query.filter_by(organizer_id=user.id).order_by(Event.start_date.desc()).all()
    
    return render_template("alumni/events.html", 
                         user=user,
                         upcoming_events=upcoming_events,
                         my_events=my_events)