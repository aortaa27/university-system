from django import forms
from django.contrib import admin

from .models import (
    Faculties, Regions, Specialties, Groups, Teachers,
    Subjects, Students, Lectures, ProgressInStudy,
    Users, Schedule, Attendance, QrSessions, Rooms,
    GradeAccess,
)

class ScheduleAdminForm(forms.ModelForm):
    Room = forms.ModelChoiceField(
        queryset=Rooms.objects.all(),
        required=False,
        label='Аудитория',
        empty_label='Выберите аудиторию'
    )

    class Meta:
        model = Schedule
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk and self.instance.Room:
            self.fields['Room'].initial = Rooms.objects.filter(Room=self.instance.Room).first()

    def clean_Room(self):
        room_obj = self.cleaned_data.get('Room')
        if room_obj:
            return room_obj.Room
        return ''


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    form = ScheduleAdminForm
    list_display = ('LectureID', 'DayOfWeek', 'StartTime', 'EndTime', 'Room', 'LessonType')
    list_filter = ('DayOfWeek', 'LessonType')
    search_fields = ('Room',)


@admin.register(Rooms)
class RoomsAdmin(admin.ModelAdmin):
    list_display = ('Room', 'QrToken', 'QrImage')
    search_fields = ('Room', 'QrToken')


@admin.register(GradeAccess)
class GradeAccessAdmin(admin.ModelAdmin):
    list_display = ('Semester', 'ControlType', 'IsOpen', 'StartDate', 'EndDate')
    list_filter = ('Semester', 'ControlType', 'IsOpen')
    search_fields = ('Semester',)

admin.site.register(Faculties)
admin.site.register(Regions)
admin.site.register(Specialties)
admin.site.register(Groups)
admin.site.register(Teachers)
admin.site.register(Subjects)
admin.site.register(Students)
admin.site.register(Lectures)
@admin.register(ProgressInStudy)
class ProgressInStudyAdmin(admin.ModelAdmin):
    list_display = ('StudentID', 'SubjectID', 'Semester', 'Module', 'ControlType', 'Grade', 'CreatedAt')
    list_filter = ('Semester', 'Module', 'ControlType', 'SubjectID')
    search_fields = ('StudentID__Student', 'StudentID__Name', 'SubjectID__Subject', 'Grade')
admin.site.register(Users)
admin.site.register(Attendance)
admin.site.register(QrSessions)
