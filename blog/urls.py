from django.urls import path
from . import views

app_name = "blog"

urlpatterns = [
    path("", views.post_list, name="post_list"),
    path("tag/<slug:tag_slug>/", views.post_list, name="post_list_by_tag"),
    path("<int:year>/<int:month>/<int:day>/<slug:post>/", views.post_detail, name="post_detail"),
    path("<int:post_id>/share/", views.post_share, name="post_share"),
    path("<int:post_id>/comment/", views.post_comment, name="post_comment"),
    path("<int:post_id>/like/", views.like_post, name="like_post"),
    path("<int:post_id>/bookmark/", views.bookmark_post, name="bookmark_post"),
    path("<int:post_id>/edit/", views.edit_post, name="edit_post"),
    path("<int:post_id>/delete/", views.delete_post, name="delete_post"),
    path("bookmarks/", views.my_bookmarks, name="my_bookmarks"),
    path("follow/<str:username>/", views.follow_user, name="follow_user"),
    path("notifications/", views.notifications_view, name="notifications"),
    path("profile/<str:username>/", views.user_profile, name="user_profile"),
    path("settings/", views.settings_view, name="settings"),
    path("signup/", views.signup_view, name="signup"),
    path("verify-otp/", views.verify_otp, name="verify_otp"),
    path("login/", views.login_view, name="login_view"),
    path("logout/", views.logout_view, name="logout"),
    path("create-post/", views.create_post, name="create_post"),
    path("search/", views.post_search, name="post_search"),
]