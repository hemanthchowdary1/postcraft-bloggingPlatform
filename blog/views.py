from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.mail import send_mail
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.contrib.auth.models import User
from taggit.models import Tag
from .models import Post, Like, OTPVerification, Bookmark, Follow, Notification
from .forms import EmailPostForm, CommentForm, SignUpForm, PostForm, EditPostForm, UserSettingsForm
from django.utils.text import slugify
from django.db.models import Q
from django.http import JsonResponse
from decouple import config


def post_list(request, tag_slug=None):
    post_list = Post.published.all()
    tag = None

    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        post_list = post_list.filter(tags__in=[tag])

    paginator = Paginator(post_list, 5)
    page_number = request.GET.get("page")

    try:
        posts = paginator.page(page_number)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)

    return render(request, "list.html", {"posts": posts, "tag": tag})


def post_detail(request, year, month, day, post):
    post = get_object_or_404(
        Post,
        status=Post.Status.PUBLISHED,
        slug=post,
        publish__year=year,
        publish__month=month,
        publish__day=day
    )

    comments = post.comments.filter(active=True)
    form = CommentForm()
    post_tags_ids = post.tags.values_list("id", flat=True)
    related_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)
    related_posts = related_posts.annotate(
        same_tags=Count("tags")
    ).order_by("-same_tags", "-publish")[:4]

    is_bookmarked = False
    is_liked = False
    if request.user.is_authenticated:
        is_bookmarked = Bookmark.objects.filter(user=request.user, post=post).exists()
        is_liked = Like.objects.filter(user=request.user, post=post).exists()

    return render(request, "detail.html", {
        "post": post,
        "comments": comments,
        "form": form,
        "related_posts": related_posts,
        "is_bookmarked": is_bookmarked,
        "is_liked": is_liked,
    })


def post_share(request, post_id):
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    sent = False

    if request.method == "POST":
        form = EmailPostForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{cd['name']} recommends you read {post.title}"
            message = f"Read {post.title} at {post_url}\n\n{cd['comments']}"
            send_mail(subject, message, cd["email"], [cd["to"]])
            sent = True
    else:
        form = EmailPostForm()

    return render(request, "share.html", {"post": post, "form": form, "sent": sent})


@login_required
def post_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    form = CommentForm(data=request.POST)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.user = request.user
        comment.save()

        if request.user != post.author:
            Notification.objects.create(
                recipient=post.author,
                sender=request.user,
                notif_type=Notification.Type.COMMENT,
                post=post
            )
    else:
        messages.error(request, "Your comment could not be posted. Please try again.")

    return redirect(post.get_absolute_url())


@login_required
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    like, created = Like.objects.get_or_create(user=request.user, post=post)

    if not created:
        like.delete()
        liked = False
    else:
        liked = True
        if request.user != post.author:
            Notification.objects.get_or_create(
                recipient=post.author,
                sender=request.user,
                notif_type=Notification.Type.LIKE,
                post=post
            )

    if is_ajax:
        return JsonResponse({'liked': liked, 'total_likes': post.total_likes()})

    return redirect(post.get_absolute_url())


@login_required
def bookmark_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    bookmark, created = Bookmark.objects.get_or_create(user=request.user, post=post)

    if not created:
        bookmark.delete()
        bookmarked = False
    else:
        bookmarked = True

    if is_ajax:
        return JsonResponse({'bookmarked': bookmarked})

    return redirect(post.get_absolute_url())


@login_required
def my_bookmarks(request):
    bookmarks = Bookmark.objects.filter(user=request.user).select_related('post')
    return render(request, "bookmarks.html", {"bookmarks": bookmarks})


@login_required
def follow_user(request, username):
    target_user = get_object_or_404(User, username=username)
    if target_user == request.user:
        return redirect("blog:user_profile", username=username)

    follow, created = Follow.objects.get_or_create(follower=request.user, following=target_user)
    if not created:
        follow.delete()
    else:
        Notification.objects.create(
            recipient=target_user,
            sender=request.user,
            notif_type=Notification.Type.FOLLOW
        )
    return redirect("blog:user_profile", username=username)


@login_required
def notifications_view(request):
    notifications = request.user.notifications.select_related('sender', 'post').all()
    notifications.filter(is_read=False).update(is_read=True)
    return render(request, "notifications.html", {"notifications": notifications})


def user_profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    posts = Post.published.filter(author=profile_user)
    followers_count = profile_user.followers.count()
    following_count = profile_user.following.count()

    is_following = False
    if request.user.is_authenticated and request.user != profile_user:
        is_following = Follow.objects.filter(follower=request.user, following=profile_user).exists()

    return render(request, "profile.html", {
        "profile_user": profile_user,
        "posts": posts,
        "followers_count": followers_count,
        "following_count": following_count,
        "is_following": is_following,
    })


@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, author=request.user)

    if request.method == "POST":
        form = EditPostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.slug = slugify(post.title)
            post.save()
            form.save_m2m()
            messages.success(request, "Post updated successfully.")
            return redirect(post.get_absolute_url())
    else:
        form = EditPostForm(instance=post)

    return render(request, "edit_post.html", {"form": form, "post": post})


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, author=request.user)

    if request.method == "POST":
        post.delete()
        messages.success(request, "Post deleted.")
        return redirect("blog:post_list")

    return render(request, "delete_post.html", {"post": post})


@login_required
def settings_view(request):
    active_tab = request.GET.get('tab', 'profile')
    profile_form = UserSettingsForm(instance=request.user)
    password_form = PasswordChangeForm(user=request.user)

    if request.method == "POST":
        if 'update_profile' in request.POST:
            profile_form = UserSettingsForm(request.POST, instance=request.user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Profile updated successfully.")
                return redirect("blog:settings")
            active_tab = 'profile'

        elif 'change_password' in request.POST:
            password_form = PasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                password_form.save()
                update_session_auth_hash(request, password_form.user)
                messages.success(request, "Password changed successfully.")
                return redirect("blog:settings")
            active_tab = 'password'

    return render(request, "settings.html", {
        "profile_form": profile_form,
        "password_form": password_form,
        "active_tab": active_tab,
    })


def signup_view(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get("email")
            domain = email.split("@")[-1]

            try:
                import dns.resolver
                dns.resolver.resolve(domain, "MX")
            except Exception:
                form.add_error("email", f"'{domain}' does not appear to be a valid email domain.")
                return render(request, "signup.html", {"form": form})

            user = form.save(commit=False)
            user.is_active = False
            user.save()
            form.save_m2m()

            otp_obj, _ = OTPVerification.objects.get_or_create(user=user)
            otp = otp_obj.generate_otp()

            try:
                send_mail(
                    "OTP Verification — MyBlog",
                    f"Your OTP code is: {otp}\n\nThis code expires in 10 minutes.",
                    config('EMAIL_HOST_USER'),
                    [email],
                    fail_silently=False,
                )
            except Exception:
                user.delete()
                form.add_error("email", "Could not send OTP. Please check your email and try again.")
                return render(request, "signup.html", {"form": form})

            request.session["otp_user_id"] = user.id
            return redirect("blog:verify_otp")

    else:
        form = SignUpForm()

    return render(request, "signup.html", {"form": form})


def verify_otp(request):
    user_id = request.session.get("otp_user_id")
    if not user_id:
        return redirect("blog:signup")

    # Fixed: use get_object_or_404 instead of bare .get() to avoid crashes
    user = get_object_or_404(User, id=user_id)
    otp_obj = get_object_or_404(OTPVerification, user=user)

    if request.method == "POST":
        # Check lockout before even trying
        if otp_obj.is_locked_out():
            return render(request, "verify_otp.html", {
                "email": user.email,
                "error": "Too many failed attempts. Please sign up again."
            })

        entered_otp = request.POST.get("otp")
        if otp_obj.verify_otp(entered_otp):
            user.is_active = True
            user.save()
            login(request, user)
            del request.session["otp_user_id"]
            return redirect("blog:post_list")
        else:
            attempts_left = 5 - otp_obj.failed_attempts
            error = "Invalid or expired OTP. Please try again."
            if attempts_left <= 2:
                error += f" ({attempts_left} attempt{'s' if attempts_left != 1 else ''} left)"
            return render(request, "verify_otp.html", {
                "email": user.email,
                "error": error
            })

    return render(request, "verify_otp.html", {"email": user.email})


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("blog:post_list")
    else:
        form = AuthenticationForm()

    return render(request, "login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("blog:post_list")


@login_required
def create_post(request):
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.status = Post.Status.PUBLISHED
            post.slug = slugify(post.title)
            post.save()
            form.save_m2m()
            return redirect(post.get_absolute_url())
    else:
        form = PostForm()

    return render(request, "create_post.html", {"form": form})


def post_search(request):
    query = None
    results = []

    if 'query' in request.GET:
        query = request.GET.get('query')
        results = Post.published.filter(
            Q(title__icontains=query) |
            Q(body__icontains=query) |
            Q(tags__name__icontains=query)
        ).distinct()

    return render(request, "search.html", {"query": query, "results": results})