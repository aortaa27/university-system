from django.db import models
from datetime import time
from django.db import models
import io
import uuid
import qrcode

from django.core.files.base import ContentFile

class Faculties(models.Model):
    Faculty = models.CharField(max_length=255)

    class Meta:
        db_table = 'Faculties'

    def __str__(self):
        return self.Faculty


class Regions(models.Model):
    Region = models.CharField(max_length=255)

    class Meta:
        db_table = 'Regions'

    def __str__(self):
        return self.Region


class Specialties(models.Model):
    Specialty = models.CharField(max_length=255)
    FacultyID = models.ForeignKey(Faculties, on_delete=models.CASCADE, db_column='FacultyID')

    class Meta:
        db_table = 'Specialties'

    def __str__(self):
        return self.Specialty


class Groups(models.Model):
    Group = models.CharField(max_length=100)
    SpecialtyID = models.ForeignKey(Specialties, on_delete=models.CASCADE, db_column='SpecialtyID')

    class Meta:
        db_table = 'Groups'

    def __str__(self):
        return self.Group


class Teachers(models.Model):
    Teacher = models.CharField(max_length=255)
    Address = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'Teachers'

    def __str__(self):
        return self.Teacher


class Subjects(models.Model):
    Subject = models.CharField(max_length=255)

    class Meta:
        db_table = 'Subjects'

    def __str__(self):
        return self.Subject

class Students(models.Model):
    Student = models.CharField(max_length=255)
    DateBorn = models.DateField(blank=True, null=True)
    RegionID = models.ForeignKey(Regions, on_delete=models.SET_NULL, db_column='RegionID', blank=True, null=True)
    NationalityID = models.IntegerField(blank=True, null=True)
    GroupID = models.ForeignKey(Groups, on_delete=models.SET_NULL, db_column='GroupID', blank=True, null=True)
    Gender = models.CharField(max_length=20, blank=True, null=True)
    StudyForm = models.CharField(max_length=50, blank=True, null=True)
    Name = models.CharField(max_length=255, blank=True, null=True)

    AdmissionYear = models.PositiveSmallIntegerField(
        'Год поступления',
        blank=True,
        null=True
    )

    class Meta:
        db_table = 'Students'

    def __str__(self):
        return f"{self.Student} {self.Name or ''}".strip()

class Lectures(models.Model):
    TeacherID = models.ForeignKey(Teachers, on_delete=models.CASCADE, db_column='TeacherID')
    SubjectID = models.ForeignKey(Subjects, on_delete=models.CASCADE, db_column='SubjectID')
    GroupID = models.ForeignKey(Groups, on_delete=models.CASCADE, db_column='GroupID')

    class Meta:
        db_table = 'Lectures'

    def __str__(self):
        return f"{self.SubjectID} - {self.GroupID}"
class ProgressInStudy(models.Model):
    MODULE_CHOICES = [
        (1, '1 модуль'),
        (2, '2 модуль'),
    ]

    CONTROL_TYPE_CHOICES = [
        ('module', 'Модуль'),
        ('exam', 'Экзамен'),
        ('final', 'Итог'),
    ]

    StudentID = models.ForeignKey(
        Students,
        on_delete=models.CASCADE,
        db_column='StudentID'
    )
    SubjectID = models.ForeignKey(
        Subjects,
        on_delete=models.CASCADE,
        db_column='SubjectID'
    )

    Semester = models.PositiveSmallIntegerField(blank=True, null=True)
    Module = models.PositiveSmallIntegerField(
        choices=MODULE_CHOICES,
        blank=True,
        null=True
    )
    ControlType = models.CharField(
        max_length=20,
        choices=CONTROL_TYPE_CHOICES,
        default='module'
    )
    Grade = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )
    CreatedAt = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True
    )

    class Meta:
        db_table = 'ProgressInStudy'
        unique_together = ('StudentID', 'SubjectID', 'Semester', 'Module', 'ControlType')

    def __str__(self):
        return f"{self.StudentID} | {self.SubjectID} | {self.Semester} | {self.Module} | {self.Grade}"
class Users(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    ]

    Login = models.CharField(max_length=100, unique=True)
    PasswordHash = models.CharField(max_length=255)
    Role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    StudentID = models.OneToOneField(
        Students,
        on_delete=models.SET_NULL,
        db_column='StudentID',
        blank=True,
        null=True
    )
    TeacherID = models.OneToOneField(
        Teachers,
        on_delete=models.SET_NULL,
        db_column='TeacherID',
        blank=True,
        null=True
    )
    IsActive = models.BooleanField(default=True)

    class Meta:
        db_table = 'Users'

    def __str__(self):
        return self.Login

class Schedule(models.Model):
    DAY_CHOICES = [
        ('Monday', 'Понедельник'),
        ('Tuesday', 'Вторник'),
        ('Wednesday', 'Среда'),
        ('Thursday', 'Четверг'),
        ('Friday', 'Пятница'),
        ('Saturday', 'Суббота'),
    ]

    START_TIME_CHOICES = [
        (time(8, 30), '08:30'),
        (time(10, 0), '10:00'),
        (time(11, 30), '11:30'),
        (time(13, 0), '13:00'),
        (time(15, 0), '15:00'),
    ]

    END_TIME_CHOICES = [
        (time(9, 50), '09:50'),
        (time(11, 20), '11:20'),
        (time(12, 50), '12:50'),
        (time(14, 20), '14:20'),
        (time(16, 20), '16:20'),
    ]

    SEMESTER_CHOICES = [
        (1, '1 семестр'),
        (2, '2 семестр'),
        (3, '3 семестр'),
        (4, '4 семестр'),
        (5, '5 семестр'),
        (6, '6 семестр'),
        (7, '7 семестр'),
        (8, '8 семестр'),
    ]

    MODULE_CHOICES = [
        (1, '1 модуль'),
        (2, '2 модуль'),
    ]

    LectureID = models.ForeignKey(Lectures, on_delete=models.CASCADE, db_column='LectureID')
    DayOfWeek = models.CharField(max_length=20, choices=DAY_CHOICES)
    StartTime = models.TimeField(choices=START_TIME_CHOICES)
    EndTime = models.TimeField(choices=END_TIME_CHOICES)
    Room = models.CharField(max_length=50, blank=True, null=True)
    LessonType = models.CharField(max_length=50, blank=True, null=True)

    Semester = models.PositiveSmallIntegerField(
        'Семестр',
        choices=SEMESTER_CHOICES,
        blank=True,
        null=True
    )

    Module = models.PositiveSmallIntegerField(
        'Модуль',
        choices=MODULE_CHOICES,
        blank=True,
        null=True
    )

    class Meta:
        db_table = 'Schedule'

    def __str__(self):
        return f"{self.get_DayOfWeek_display()} {self.StartTime} - {self.EndTime}"
class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Присутствовал'),
        ('absent', 'Отсутствовал'),
        ('late', 'Опоздал'),
    ]

    StudentID = models.ForeignKey(Students, on_delete=models.CASCADE, db_column='StudentID')
    ScheduleID = models.ForeignKey(Schedule, on_delete=models.CASCADE, db_column='ScheduleID')
    LessonDate = models.DateField()
    Status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    MarkedByTeacherID = models.ForeignKey(
        Teachers,
        on_delete=models.SET_NULL,
        db_column='MarkedByTeacherID',
        blank=True,
        null=True
    )
    MarkedAt = models.DateTimeField(auto_now_add=True)
    QrConfirmed = models.BooleanField(default=False)

    class Meta:
        db_table = 'Attendance'
        unique_together = ('StudentID', 'ScheduleID', 'LessonDate')

    def __str__(self):
        return f"{self.StudentID} - {self.LessonDate}"

class QrSessions(models.Model):
    ScheduleID = models.ForeignKey(Schedule, on_delete=models.CASCADE, db_column='ScheduleID')
    LessonDate = models.DateField()
    QrToken = models.CharField(max_length=255, unique=True)
    CreatedAt = models.DateTimeField(auto_now_add=True)
    ExpiresAt = models.DateTimeField()
    IsActive = models.BooleanField(default=True)

    class Meta:
        db_table = 'QrSessions'

    def __str__(self):
        return self.QrToken

class Rooms(models.Model):
    Room = models.CharField(max_length=50, unique=True)
    QrToken = models.CharField(max_length=255, unique=True, blank=True)
    QrImage = models.ImageField(upload_to='room_qr/', blank=True, null=True)

    class Meta:
        db_table = 'Rooms'

    def __str__(self):
        return self.Room

    def save(self, *args, **kwargs):
        if not self.QrToken:
            self.QrToken = f"room-{self.Room}-{uuid.uuid4().hex[:8]}"

        super().save(*args, **kwargs)

        if not self.QrImage:
            qr = qrcode.make(self.QrToken)
            buffer = io.BytesIO()
            qr.save(buffer, format='PNG')
            file_name = f'room_{self.Room}.png'
            self.QrImage.save(file_name, ContentFile(buffer.getvalue()), save=False)
            buffer.close()
            super().save(update_fields=['QrImage'])

class GradeAccess(models.Model):
        CONTROL_TYPE_CHOICES = [
            ('module_1', '1 модуль'),
            ('module_2', '2 модуль'),
            ('exam', 'Экзамен'),
            ('final', 'Итог'),
        ]

        Semester = models.PositiveSmallIntegerField(
            verbose_name='Семестр'
        )

        ControlType = models.CharField(
            max_length=20,
            choices=CONTROL_TYPE_CHOICES,
            verbose_name='Тип контроля'
        )

        IsOpen = models.BooleanField(
            default=False,
            verbose_name='Открыт'
        )

        StartDate = models.DateField(
            blank=True,
            null=True,
            verbose_name='Дата начала'
        )

        EndDate = models.DateField(
            blank=True,
            null=True,
            verbose_name='Дата окончания'
        )

        class Meta:
            db_table = 'GradeAccess'
            verbose_name = 'Доступ к оценкам'
            verbose_name_plural = 'Доступ к оценкам'
            unique_together = ('Semester', 'ControlType')

        def __str__(self):
            return f'{self.Semester} семестр - {self.get_ControlType_display()}'