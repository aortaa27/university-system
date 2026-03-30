import json
from datetime import date, datetime, timedelta

from django.contrib import messages
from django.contrib.auth import logout
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone

from .models import (
    Users,
    Schedule,
    ProgressInStudy,
    Attendance,
    Lectures,
    Rooms,
    Students,
    Subjects,
    GradeAccess,
)


def login_view(request):
    if request.method == 'POST':
        login = request.POST.get('login')
        password = request.POST.get('password')

        try:
            user = Users.objects.get(
                Login=login,
                PasswordHash=password,
                IsActive=True
            )

            request.session['user_id'] = user.id
            request.session['role'] = user.Role
            request.session['login'] = user.Login

            if user.Role == 'student':
                return redirect('student_schedule')
            elif user.Role == 'teacher':
                return redirect('teacher_schedule')
            elif user.Role == 'admin':
                return redirect('/admin/')

        except Users.DoesNotExist:
            messages.error(request, 'Неверный логин или пароль')

    return render(request, 'main/login.html')


def logout_view(request):
    request.session.flush()
    logout(request)
    return redirect('login')


def student_required(request):
    if request.session.get('role') != 'student':
        return None
    return Users.objects.filter(id=request.session.get('user_id')).first()


def teacher_required(request):
    if request.session.get('role') != 'teacher':
        return None
    return Users.objects.filter(id=request.session.get('user_id')).first()


def get_current_semester(admission_year):
    today = date.today()
    current_year = today.year

    years_passed = current_year - admission_year

    if today.month >= 9:
        semester = years_passed * 2 + 1
    else:
        semester = years_passed * 2

    if semester < 1:
        semester = 1

    return semester


def get_current_semester_by_date():
    today = timezone.localdate()

    if 1 <= today.month <= 6:
        return 6
    elif 9 <= today.month <= 12:
        return 7
    else:
        return 6


def get_next_lesson_date(day_name):
    day_map = {
        'Monday': 0,
        'Tuesday': 1,
        'Wednesday': 2,
        'Thursday': 3,
        'Friday': 4,
        'Saturday': 5,
        'Sunday': 6,
    }

    today = timezone.localdate()
    today_weekday = today.weekday()
    target_weekday = day_map.get(day_name, today_weekday)

    days_ahead = target_weekday - today_weekday
    if days_ahead < 0:
        days_ahead += 7

    return today + timedelta(days=days_ahead)


def get_dates_for_weekday_in_semester(target_weekday, semester, count=18):
    year = timezone.localdate().year

    if int(semester) % 2 == 0:
        start_date = date(year, 2, 1)
    else:
        start_date = date(year, 9, 1)

    days_ahead = target_weekday - start_date.weekday()
    if days_ahead < 0:
        days_ahead += 7

    first_date = start_date + timedelta(days=days_ahead)

    dates = []
    current = first_date
    for _ in range(count):
        dates.append(current)
        current += timedelta(days=7)

    return dates


def get_dates_for_schedule(schedule, semester, count=18):
    day_map = {
        'Monday': 0,
        'Tuesday': 1,
        'Wednesday': 2,
        'Thursday': 3,
        'Friday': 4,
        'Saturday': 5,
        'Sunday': 6,
    }

    year = timezone.localdate().year

    if int(semester) % 2 == 0:
        start_date = date(year, 2, 1)
    else:
        start_date = date(year, 9, 1)

    target_weekday = day_map.get(schedule.DayOfWeek, 0)

    days_ahead = target_weekday - start_date.weekday()
    if days_ahead < 0:
        days_ahead += 7

    first_date = start_date + timedelta(days=days_ahead)

    dates = []
    current = first_date
    for _ in range(count):
        dates.append(current)
        current += timedelta(days=7)

    return dates


def find_current_or_nearest_schedule(schedules):
    if not schedules:
        return None

    now = timezone.localtime()
    today_name = now.strftime('%A')
    current_time = now.time()

    today_schedules = [s for s in schedules if s.DayOfWeek == today_name]

    for s in today_schedules:
        if s.StartTime <= current_time <= s.EndTime:
            return s

    future_today = [s for s in today_schedules if s.StartTime >= current_time]
    if future_today:
        future_today.sort(key=lambda x: x.StartTime)
        return future_today[0]

    return schedules[0]


def student_schedule(request):
    user = student_required(request)
    if not user:
        return redirect('login')

    student = user.StudentID
    selected_day = request.GET.get('day') or timezone.localdate().strftime('%A')
    selected_semester = request.GET.get('semester')

    admission_year = student.AdmissionYear or 2023
    current_semester = get_current_semester(admission_year)

    schedules = []

    if student and student.GroupID:
        lectures = Lectures.objects.filter(GroupID=student.GroupID)
        lecture_ids = lectures.values_list('id', flat=True)

        schedules = Schedule.objects.filter(
            LectureID__in=lecture_ids
        ).select_related(
            'LectureID',
            'LectureID__SubjectID',
            'LectureID__GroupID'
        ).order_by('StartTime')

        if selected_semester:
            schedules = schedules.filter(Semester=selected_semester)
        else:
            schedules = schedules.filter(Semester=current_semester)

        if selected_day:
            schedules = schedules.filter(DayOfWeek=selected_day)

    day_choices = [
        ('Monday', 'Понедельник'),
        ('Tuesday', 'Вторник'),
        ('Wednesday', 'Среда'),
        ('Thursday', 'Четверг'),
        ('Friday', 'Пятница'),
        ('Saturday', 'Суббота'),
    ]

    semesters = range(1, 9)

    return render(request, 'main/student_schedule.html', {
        'login': request.session.get('login'),
        'student': student,
        'schedules': schedules,
        'day_choices': day_choices,
        'selected_day': selected_day,
        'selected_semester': selected_semester or str(current_semester),
        'current_semester': current_semester,
        'semesters': semesters,
        'active_page': 'schedule',
    })

def student_progress(request):
    user = student_required(request)
    if not user:
        return redirect('login')

    student = user.StudentID
    admission_year = student.AdmissionYear or 2023
    current_semester = get_current_semester(admission_year)

    selected_subject = request.GET.get('subject')
    selected_semester = request.GET.get('semester')

    progress_qs = ProgressInStudy.objects.filter(
        StudentID=student
    ).select_related('SubjectID')

    if selected_semester:
        progress_qs = progress_qs.filter(Semester=selected_semester)
    else:
        progress_qs = progress_qs.filter(Semester=current_semester)

    if selected_subject:
        progress_qs = progress_qs.filter(SubjectID_id=selected_subject)

    progress_qs = progress_qs.order_by('SubjectID__Subject', 'ControlType', 'Module')

    subjects = Subjects.objects.filter(
        lectures__GroupID=student.GroupID
    ).distinct().order_by('Subject')

    progress_map = {}

    for item in progress_qs:
        subject_id = item.SubjectID_id

        if subject_id not in progress_map:
            progress_map[subject_id] = {
                'subject': item.SubjectID,
                'module_1': '',
                'module_2': '',
                'exam': '',
                'final': '',
            }

        if item.ControlType == 'module':
            if item.Module == 1:
                progress_map[subject_id]['module_1'] = item.Grade or ''
            elif item.Module == 2:
                progress_map[subject_id]['module_2'] = item.Grade or ''
        elif item.ControlType == 'exam':
            progress_map[subject_id]['exam'] = item.Grade or ''
        elif item.ControlType == 'final':
            progress_map[subject_id]['final'] = item.Grade or ''

    progress_rows = list(progress_map.values())

    semesters = range(1, 9)

    return render(request, 'main/student_progress.html', {
        'login': request.session.get('login'),
        'student': student,
        'progress_rows': progress_rows,
        'subjects': subjects,
        'selected_subject': selected_subject,
        'selected_semester': selected_semester or str(current_semester),
        'semesters': semesters,
        'current_semester': current_semester,
        'active_page': 'progress',
    })
def student_attendance(request):
    user = student_required(request)
    if not user:
        return redirect('login')

    student = user.StudentID
    admission_year = student.AdmissionYear or 2023
    current_semester = get_current_semester(admission_year)

    selected_subject = request.GET.get('subject')
    selected_status = request.GET.get('status')
    selected_semester = request.GET.get('semester')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    attendance_list = Attendance.objects.filter(
        StudentID=student
    ).select_related(
        'ScheduleID',
        'ScheduleID__LectureID',
        'ScheduleID__LectureID__SubjectID'
    )

    if selected_semester:
        attendance_list = attendance_list.filter(ScheduleID__Semester=selected_semester)
    else:
        attendance_list = attendance_list.filter(ScheduleID__Semester=current_semester)

    if selected_subject:
        attendance_list = attendance_list.filter(
            ScheduleID__LectureID__SubjectID_id=selected_subject
        )

    if selected_status:
        attendance_list = attendance_list.filter(Status=selected_status)

    if date_from:
        attendance_list = attendance_list.filter(LessonDate__gte=date_from)

    if date_to:
        attendance_list = attendance_list.filter(LessonDate__lte=date_to)

    attendance_list = attendance_list.order_by(
        '-LessonDate',
        '-ScheduleID__StartTime'
    )

    subjects = Subjects.objects.filter(
        lectures__GroupID=student.GroupID
    ).distinct()

    semesters = range(1, 9)

    return render(request, 'main/student_attendance.html', {
        'login': request.session.get('login'),
        'student': student,
        'attendance_list': attendance_list,
        'subjects': subjects,
        'selected_subject': selected_subject,
        'selected_status': selected_status,
        'selected_semester': selected_semester or str(current_semester),
        'date_from': date_from,
        'date_to': date_to,
        'semesters': semesters,
        'current_semester': current_semester,
        'active_page': 'attendance',
    })
def student_profile(request):
    user = student_required(request)
    if not user:
        return redirect('login')

    return render(request, 'main/student_profile.html', {
        'user': user,
        'student': user.StudentID,
        'login': request.session.get('login'),
        'active_page': 'profile',
    })


def scan_qr(request, schedule_id):
    user = student_required(request)
    if not user:
        return redirect('login')

    schedule = Schedule.objects.filter(id=schedule_id).select_related(
        'LectureID',
        'LectureID__SubjectID',
        'LectureID__GroupID'
    ).first()

    if not schedule:
        return redirect('student_schedule')

    return render(request, 'main/scan_qr.html', {
        'login': request.session.get('login'),
        'student': user.StudentID,
        'schedule': schedule,
        'active_page': 'schedule',
    })


def qr_submit(request, schedule_id):
    user = student_required(request)
    if not user:
        return JsonResponse({'success': False, 'message': 'Ошибка авторизации'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Неверный метод запроса'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Некорректные данные'}, status=400)

    token = data.get('qr_token')
    if not token:
        return JsonResponse({'success': False, 'message': 'QR токен не передан'}, status=400)

    room = Rooms.objects.filter(QrToken=token).first()
    if not room:
        return JsonResponse({'success': False, 'message': 'Неверный QR код'})

    schedule = Schedule.objects.filter(id=schedule_id).select_related(
        'LectureID',
        'LectureID__GroupID',
        'LectureID__SubjectID'
    ).first()

    if not schedule:
        return JsonResponse({'success': False, 'message': 'Пара не найдена'})

    if schedule.Room != room.Room:
        return JsonResponse({'success': False, 'message': 'Вы сканируете не ту аудиторию'})

    if not user.StudentID or not user.StudentID.GroupID:
        return JsonResponse({'success': False, 'message': 'У студента не указана группа'})

    if user.StudentID.GroupID != schedule.LectureID.GroupID:
        return JsonResponse({'success': False, 'message': 'Это не ваша пара'})

    now = timezone.localtime()
    today = now.date()

    lesson_start = datetime.combine(today, schedule.StartTime)
    lesson_end = datetime.combine(today, schedule.EndTime)

    lesson_start = timezone.make_aware(lesson_start, timezone.get_current_timezone())
    lesson_end = timezone.make_aware(lesson_end, timezone.get_current_timezone())

    if now < lesson_start:
        return JsonResponse({'success': False, 'message': 'Пара еще не началась'})
    if now > lesson_end:
        return JsonResponse({'success': False, 'message': 'Пара уже закончилась'})

    attendance, created = Attendance.objects.get_or_create(
        StudentID=user.StudentID,
        ScheduleID=schedule,
        LessonDate=today,
        defaults={
            'Status': 'present',
            'QrConfirmed': True,
        }
    )

    if not created:
        if attendance.QrConfirmed:
            return JsonResponse({'success': False, 'message': 'Вы уже отмечены'})
        attendance.Status = 'present'
        attendance.QrConfirmed = True
        attendance.save(update_fields=['Status', 'QrConfirmed'])

    return JsonResponse({
        'success': True,
        'message': 'Вы успешно отметились на занятии'
    })


def teacher_schedule(request):
    user = teacher_required(request)
    if not user:
        return redirect('login')

    selected_day = request.GET.get('day') or timezone.localdate().strftime('%A')
    selected_semester = request.GET.get('semester')

    current_semester = get_current_semester_by_date()
    schedules = []

    if user.TeacherID:
        lectures = Lectures.objects.filter(TeacherID=user.TeacherID)
        lecture_ids = lectures.values_list('id', flat=True)

        schedules = Schedule.objects.filter(
            LectureID__in=lecture_ids
        ).select_related(
            'LectureID',
            'LectureID__SubjectID',
            'LectureID__GroupID'
        ).order_by('StartTime')

        if selected_semester:
            schedules = schedules.filter(Semester=selected_semester)
        else:
            schedules = schedules.filter(Semester=current_semester)

        if selected_day:
            schedules = schedules.filter(DayOfWeek=selected_day)

    day_choices = [
        ('Monday', 'Понедельник'),
        ('Tuesday', 'Вторник'),
        ('Wednesday', 'Среда'),
        ('Thursday', 'Четверг'),
        ('Friday', 'Пятница'),
        ('Saturday', 'Суббота'),
    ]

    semesters = range(1, 9)

    return render(request, 'main/teacher_schedule.html', {
        'login': request.session.get('login'),
        'teacher': user.TeacherID,
        'schedules': schedules,
        'day_choices': day_choices,
        'selected_day': selected_day,
        'selected_semester': selected_semester or str(current_semester),
        'current_semester': current_semester,
        'semesters': semesters,
        'active_page': 'schedule',
    })
def teacher_journal(request):
    user = teacher_required(request)
    if not user:
        return redirect('login')

    if not user.TeacherID:
        return redirect('teacher_schedule')

    current_semester = get_current_semester_by_date()

    selected_semester = request.GET.get('semester') or request.POST.get('semester') or str(current_semester)
    selected_group_id = request.GET.get('group') or request.POST.get('group_id')
    selected_subject_id = request.GET.get('subject') or request.POST.get('subject_id')

    teacher_schedules_qs = Schedule.objects.filter(
        LectureID__TeacherID=user.TeacherID
    ).select_related(
        'LectureID',
        'LectureID__SubjectID',
        'LectureID__GroupID'
    )

    if selected_semester:
        teacher_schedules_qs = teacher_schedules_qs.filter(Semester=selected_semester)

    teacher_schedules_qs = teacher_schedules_qs.order_by(
        'LectureID__GroupID__Group',
        'LectureID__SubjectID__Subject',
        'DayOfWeek',
        'StartTime'
    )

    teacher_schedules = list(teacher_schedules_qs)

    groups = []
    seen_group_ids = set()
    for schedule in teacher_schedules:
        group = schedule.LectureID.GroupID
        if group and group.id not in seen_group_ids:
            groups.append(group)
            seen_group_ids.add(group.id)

    subjects = []
    seen_subject_ids = set()
    for schedule in teacher_schedules:
        subject = schedule.LectureID.SubjectID
        if subject and subject.id not in seen_subject_ids:
            subjects.append(subject)
            seen_subject_ids.add(subject.id)

    selected_group = None
    if selected_group_id:
        for group in groups:
            if str(group.id) == str(selected_group_id):
                selected_group = group
                break

    if not selected_group and groups:
        auto_schedule = find_current_or_nearest_schedule(teacher_schedules)
        if auto_schedule:
            selected_group = auto_schedule.LectureID.GroupID
        else:
            selected_group = groups[0]

    selected_subject = None
    if selected_subject_id:
        for subject in subjects:
            if str(subject.id) == str(selected_subject_id):
                selected_subject = subject
                break

    if not selected_subject and subjects:
        auto_schedule = find_current_or_nearest_schedule(teacher_schedules)
        if auto_schedule:
            selected_subject = auto_schedule.LectureID.SubjectID
        else:
            selected_subject = subjects[0]

    today = timezone.localdate()

    module_1_open = False
    module_2_open = False
    exam_open = False
    final_open = False

    access_records = GradeAccess.objects.filter(Semester=selected_semester)

    for access in access_records:
        is_in_period = True

        if access.StartDate and today < access.StartDate:
            is_in_period = False
        if access.EndDate and today > access.EndDate:
            is_in_period = False

        if access.IsOpen and is_in_period:
            if access.ControlType == 'module_1':
                module_1_open = True
            elif access.ControlType == 'module_2':
                module_2_open = True
            elif access.ControlType == 'exam':
                exam_open = True
            elif access.ControlType == 'final':
                final_open = True

    students_data = []
    students = []

    if selected_group:
        students = list(
            Students.objects.filter(
                GroupID=selected_group
            ).order_by('Student', 'Name')
        )

    existing_progress = {}

    if selected_group and selected_subject and selected_semester:
        progress_qs = ProgressInStudy.objects.filter(
            StudentID__GroupID=selected_group,
            SubjectID=selected_subject,
            Semester=selected_semester
        ).select_related('StudentID')

        for item in progress_qs:
            sid = item.StudentID_id

            if sid not in existing_progress:
                existing_progress[sid] = {
                    'module_1': '',
                    'module_2': '',
                    'exam': '',
                    'final': '',
                }

            if item.ControlType == 'module':
                if item.Module == 1:
                    existing_progress[sid]['module_1'] = item.Grade or ''
                elif item.Module == 2:
                    existing_progress[sid]['module_2'] = item.Grade or ''
            elif item.ControlType == 'exam':
                existing_progress[sid]['exam'] = item.Grade or ''
            elif item.ControlType == 'final':
                existing_progress[sid]['final'] = item.Grade or ''

    if request.method == 'POST':
        if not selected_group or not selected_subject or not selected_semester:
            messages.error(request, 'Выберите семестр, группу и предмет.')
            return redirect('teacher_journal')

        saved_count = 0

        for student in students:
            module_1 = request.POST.get(f'module_1_{student.id}', '').strip()
            module_2 = request.POST.get(f'module_2_{student.id}', '').strip()
            exam = request.POST.get(f'exam_{student.id}', '').strip()
            final = request.POST.get(f'final_{student.id}', '').strip()

            if module_1 and module_1_open:
                ProgressInStudy.objects.update_or_create(
                    StudentID=student,
                    SubjectID=selected_subject,
                    Semester=int(selected_semester),
                    Module=1,
                    ControlType='module',
                    defaults={'Grade': module_1}
                )
                saved_count += 1

            if module_2 and module_2_open:
                ProgressInStudy.objects.update_or_create(
                    StudentID=student,
                    SubjectID=selected_subject,
                    Semester=int(selected_semester),
                    Module=2,
                    ControlType='module',
                    defaults={'Grade': module_2}
                )
                saved_count += 1

            if exam and exam_open:
                ProgressInStudy.objects.update_or_create(
                    StudentID=student,
                    SubjectID=selected_subject,
                    Semester=int(selected_semester),
                    Module=None,
                    ControlType='exam',
                    defaults={'Grade': exam}
                )
                saved_count += 1

            if final and final_open:
                ProgressInStudy.objects.update_or_create(
                    StudentID=student,
                    SubjectID=selected_subject,
                    Semester=int(selected_semester),
                    Module=None,
                    ControlType='final',
                    defaults={'Grade': final}
                )
                saved_count += 1

        if saved_count > 0:
            messages.success(request, f'Журнал сохранен. Обновлено записей: {saved_count}')
        else:
            messages.warning(request, 'Нет доступных полей для сохранения. Возможно, доступ закрыт администратором.')

        return redirect(
            f'/teacher/journal/?semester={selected_semester}'
            f'&group={selected_group.id}'
            f'&subject={selected_subject.id}'
        )

    for student in students:
        progress = existing_progress.get(student.id, {
            'module_1': '',
            'module_2': '',
            'exam': '',
            'final': '',
        })

        students_data.append({
            'student': student,
            'module_1': progress['module_1'],
            'module_2': progress['module_2'],
            'exam': progress['exam'],
            'final': progress['final'],
        })

    semesters = range(1, 9)

    return render(request, 'main/teacher_journal.html', {
        'login': request.session.get('login'),
        'teacher': user.TeacherID,
        'active_page': 'journal',
        'semesters': semesters,
        'current_semester': current_semester,
        'selected_semester': str(selected_semester),
        'groups': groups,
        'selected_group': selected_group,
        'subjects': subjects,
        'selected_subject': selected_subject,
        'students_data': students_data,
        'module_1_open': module_1_open,
        'module_2_open': module_2_open,
        'exam_open': exam_open,
        'final_open': final_open,
    })
def teacher_attendance(request):
    user = teacher_required(request)
    if not user:
        return redirect('login')

    if not user.TeacherID:
        return redirect('teacher_schedule')

    current_semester = get_current_semester_by_date()

    selected_semester = request.GET.get('semester') or request.POST.get('semester') or str(current_semester)
    selected_group_id = request.GET.get('group') or request.POST.get('group_id')
    selected_schedule_id = request.GET.get('schedule') or request.POST.get('schedule_id')
    selected_lesson_date = request.GET.get('lesson_date') or request.POST.get('lesson_date')

    teacher_schedules_qs = Schedule.objects.filter(
        LectureID__TeacherID=user.TeacherID
    ).select_related(
        'LectureID',
        'LectureID__SubjectID',
        'LectureID__GroupID'
    )

    if selected_semester:
        teacher_schedules_qs = teacher_schedules_qs.filter(Semester=selected_semester)

    teacher_schedules_qs = teacher_schedules_qs.order_by(
        'LectureID__GroupID__Group',
        'DayOfWeek',
        'StartTime'
    )

    teacher_schedules = list(teacher_schedules_qs)

    groups = []
    seen_group_ids = set()
    for schedule in teacher_schedules:
        group = schedule.LectureID.GroupID
        if group and group.id not in seen_group_ids:
            groups.append(group)
            seen_group_ids.add(group.id)

    selected_group = None
    if selected_group_id:
        for group in groups:
            if str(group.id) == str(selected_group_id):
                selected_group = group
                break

    if not selected_group and groups:
        auto_schedule = find_current_or_nearest_schedule(teacher_schedules)
        if auto_schedule:
            selected_group = auto_schedule.LectureID.GroupID
        else:
            selected_group = groups[0]

    filtered_schedules = []
    if selected_group:
        filtered_schedules = [
            s for s in teacher_schedules
            if s.LectureID.GroupID_id == selected_group.id
        ]

    selected_schedule = None
    if selected_schedule_id:
        for schedule in filtered_schedules:
            if str(schedule.id) == str(selected_schedule_id):
                selected_schedule = schedule
                break

    if not selected_schedule and filtered_schedules:
        selected_schedule = find_current_or_nearest_schedule(filtered_schedules)
    lesson_dates = []
    selected_date_obj = None

    if selected_schedule:
        all_lesson_dates = get_dates_for_schedule(
            selected_schedule,
            selected_semester,
            count=18
        )

        today = timezone.localdate()

        # Показываем только уже наступившие даты
        lesson_dates = [d for d in all_lesson_dates if d <= today]

        # Если вообще еще не было ни одного занятия — список пустой
        # Тогда ничего не выбираем
        if selected_lesson_date:
            try:
                selected_date_obj = datetime.strptime(
                    selected_lesson_date,
                    '%Y-%m-%d'
                ).date()
            except ValueError:
                selected_date_obj = None

        # Не даем выбрать будущую дату вручную через URL
        if selected_date_obj and selected_date_obj not in lesson_dates:
            selected_date_obj = None

        # По умолчанию берем сегодняшнюю дату, если она есть,
        # иначе последнюю прошедшую
        if not selected_date_obj and lesson_dates:
            if today in lesson_dates:
                selected_date_obj = today
            else:
                selected_date_obj = lesson_dates[-1]
    if request.method == 'POST':
        if not selected_schedule or not selected_date_obj:
            messages.error(request, 'Выберите группу, дату и занятие')
            return redirect('teacher_attendance')

        students = Students.objects.filter(
            GroupID=selected_schedule.LectureID.GroupID
        ).order_by('Student', 'Name')

        for student in students:
            field_name = f'status_{student.id}_{selected_date_obj.strftime("%Y-%m-%d")}'
            status_value = request.POST.get(field_name)

            if not status_value:
                continue

            attendance, created = Attendance.objects.get_or_create(
                StudentID=student,
                ScheduleID=selected_schedule,
                LessonDate=selected_date_obj,
                defaults={
                    'Status': status_value,
                    'MarkedByTeacherID': user.TeacherID,
                    'QrConfirmed': status_value == 'present',
                }
            )

            if not created:
                attendance.Status = status_value
                attendance.MarkedByTeacherID = user.TeacherID
                attendance.QrConfirmed = (status_value == 'present')
                attendance.save(
                    update_fields=['Status', 'MarkedByTeacherID', 'QrConfirmed']
                )

        messages.success(request, 'Посещаемость сохранена')
        return redirect(
            f'/teacher/attendance/?semester={selected_semester}'
            f'&group={selected_group.id}'
            f'&schedule={selected_schedule.id}'
            f'&lesson_date={selected_date_obj.strftime("%Y-%m-%d")}'
        )

    table_rows = []
    totals = []
    students = []

    if selected_schedule and selected_date_obj:
        students = Students.objects.filter(
            GroupID=selected_schedule.LectureID.GroupID
        ).order_by('Student', 'Name')

        attendance_qs = Attendance.objects.filter(
            ScheduleID=selected_schedule,
            LessonDate=selected_date_obj
        ).select_related('StudentID')

        attendance_map = {}
        for item in attendance_qs:
            attendance_map[item.StudentID_id] = item

        present_count = 0

        for student in students:
            att = attendance_map.get(student.id)
            status = att.Status if att else ''

            if status == 'present':
                present_count += 1

            table_rows.append({
                'student': student,
                'status': status,
                'date': selected_date_obj,
            })

        totals = [present_count]

    semesters = range(1, 9)

    return render(request, 'main/teacher_attendance.html', {
        'login': request.session.get('login'),
        'teacher': user.TeacherID,
        'active_page': 'attendance',
        'semesters': semesters,
        'current_semester': current_semester,
        'selected_semester': str(selected_semester),
        'groups': groups,
        'selected_group': selected_group,
        'teacher_schedules': filtered_schedules,
        'selected_schedule': selected_schedule,
        'lesson_dates': lesson_dates,
        'selected_lesson_date': selected_date_obj,
        'table_rows': table_rows,
        'totals': totals,
    })


def teacher_profile(request):
    user = teacher_required(request)
    if not user:
        return redirect('login')

    teacher_lectures = Lectures.objects.filter(
        TeacherID=user.TeacherID
    ).select_related('SubjectID', 'GroupID')

    return render(request, 'main/teacher_profile.html', {
        'login': request.session.get('login'),
        'teacher': user.TeacherID,
        'teacher_lectures': teacher_lectures,
        'active_page': 'profile',
    })
