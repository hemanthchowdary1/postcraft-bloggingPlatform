from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from taggit.managers import TaggableManager
import random
import string


class PublishManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=Post.Status.PUBLISHED)


class Post(models.Model):

    class Status(models.TextChoices):
        DRAFT = "DF", "Draft"
        PUBLISHED = "PB", "Published"

    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=250, unique_for_date='publish')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="blog_posts")
    body = models.TextField()
    image = models.ImageField(upload_to='posts/%Y/%m/%d/', blank=True, null=True)
    publish = models.DateTimeField(default=timezone.now)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=2, choices=Status.choices, default=Status.DRAFT)

    objects = models.Manager()
    published = PublishManager()
    tags = TaggableManager()

    class Meta:
        ordering = ['-publish']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse(
            "blog:post_detail",
            args=[self.publish.year, self.publish.month, self.publish.day, self.slug]
        )

    def total_likes(self):
        return self.likes.count()


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    body = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['created']

    def __str__(self):
        return f"Comment by {self.user} on {self.post}"


class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')

    def __str__(self):
        return f"{self.user} likes {self.post}"


class OTPVerification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="otp_verification")
    otp_code = models.CharField(max_length=6)
    created = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    failed_attempts = models.IntegerField(default=0)  # brute force protection

    def generate_otp(self):
        self.otp_code = ''.join(random.choices(string.digits, k=6))
        self.created = timezone.now()
        self.is_verified = False
        self.failed_attempts = 0  # reset on new OTP
        self.save()
        return self.otp_code

    def is_expired(self):
        expiry_time = self.created + timezone.timedelta(minutes=10)
        return timezone.now() > expiry_time

    def verify_otp(self, entered_otp):
        # Lock out after 5 failed attempts
        if self.failed_attempts >= 5:
            return False

        if not self.is_expired() and self.otp_code == entered_otp and not self.is_verified:
            self.is_verified = True
            self.save()
            return True

        # Wrong code — increment failed attempts
        self.failed_attempts += 1
        self.save()
        return False

    def is_locked_out(self):
        return self.failed_attempts >= 5


class Bookmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookmarks")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="bookmarked_by")
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')

    def __str__(self):
        return f"{self.user} bookmarked {self.post}"


class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name="following")
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name="followers")
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')

    def __str__(self):
        return f"{self.follower} follows {self.following}"


class Notification(models.Model):

    class Type(models.TextChoices):
        LIKE = "LK", "liked your post"
        COMMENT = "CM", "commented on your post"
        FOLLOW = "FL", "started following you"

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_notifications")
    notif_type = models.CharField(max_length=2, choices=Type.choices)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return f"{self.sender} {self.get_notif_type_display()} — {self.recipient}"