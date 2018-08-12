from django.db import models


class Person(models.Model):
    user_id = models.PositiveIntegerField()
    language = models.CharField(max_length=8)

    @classmethod
    def create(cls, user_id):
        person = cls(user_id=user_id)
        person.save()
        return person

    def __str__(self):
        return self.user_id


class Task(models.Model):
    title = models.CharField(max_length=42)
    description = models.CharField(max_length=4096)
    short_description = models.CharField(max_length=126)
    done = models.BooleanField(default=False)

    owner = models.ForeignKey(
        Person,
        related_name='task_owner',
        on_delete=models.CASCADE
    )

    @classmethod
    def create(cls, title, description, owner):
        task = cls(title=title, description=description, owner=owner)
        task.save()
        return task

    def save(self, *args, **kwargs):
        self.short_description = self.description[:126]
        super().save(*args, **kwargs)
