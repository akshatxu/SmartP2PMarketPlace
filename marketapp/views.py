from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from datetime import datetime
from forms import *
from models import *
from django.contrib.auth.hashers import make_password, check_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
import smtplib
from email.mime.text import MIMEText as text
import cloudinary
import cloudinary.uploader
import cloudinary.api
from marketplace.settings import BASE_DIR
import os

cloudinary.config(
  cloud_name = "sarthakn",
  api_key = "262496684599191",
  api_secret = "W3DeVlkagZImIYWqOggidrGtg2U"
)

# View to the landing page
def landing(request):
    return render(request,'landing.html')


# View to the home page

def signup(request):
    today = datetime.now()
    if request.method == 'POST':
        signup_form = SignUpForm(request.POST)

        if signup_form.is_valid():
            # Extract the details from the form
            username = signup_form.cleaned_data['username']
            name = signup_form.cleaned_data['name']
            email = signup_form.cleaned_data['email']
            password = signup_form.cleaned_data['password']

            #Saving data to the database
            user = UserModel(name=name, password=make_password(password), email=email, username=username)
            user.save()

            # Send an email to the user on successful sign up
            # send_email('smartp2pmarketplace.com',
            #             email,
            #             'Thanks for being a part of my Smart P2P Marketplace. You are awesome :)',
            #             'Welcome')
            # try:
            send_mail(
                    'Welcome',
                    'Thanks for being a part of my Smart P2P Marketplace. You are awesome :)',
                    'smartp2pmarketplace.com',
                    [email],
                    fail_silently=False,
                    )
            # To prevent header injection https://docs.djangoproject.com/es/1.11/topics/email/#preventing-header-injection
            # except BadHeaderError:
                # return HttpResponse('Invalid header found')



            #Show the success page
            return render(request, 'success.html')
        else:
            print 'Error occured while signing up'
            return render(request,'home.html',{'context': signup_form.errors})

    else:
        signup_form = SignUpForm()

    # Render the home page
    return render(request,'home.html',{'signup_form': signup_form})


# def send_email(sender,receiver,message,subject):
#     sender = sender
#     receivers = receiver
#     m = text(message)
#     m['Subject'] = subject
#     m['From'] = sender
#     m['To'] = receiver
#     # message = message
#     try:
#         smtpObj = smtplib.SMTP('localhost')
#         smtpObj.sendmail(sender, receivers, str(m))
#         print "Successfully sent email"
#     except smtplib.SMTPException:
#         print "Error: unable to send email"

# View for the login page

def login(request):

    dict = {}

    if request.method == 'POST':

        form = LoginForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            user = UserModel.objects.filter(username=username).first()


            if user:
                if check_password(password, user.password):
                    # User is Valid
                    print 'Valid'
                    token   =  SessionToken(user=user)
                    token.create_token()
                    token.save()



                    response = redirect('/feed/')

                    response.set_cookie(key='session_token', value=token.session_token)
                    return response


                else:
                    # User is not valid
                    print 'Invalid User'
                    return render(request,'login.html',{'context': 'Your password is not correct! Try Again!'})
            else:
                # User does not exist'
                print 'User doesnt exist'
                return render(request,'login.html',{'context': 'Username not registered'})
        else:
            # Form is not Valid
            print 'Invalid Form'
            return render(request,'login.html',{'context': 'Could not log you in. Please fill all the fields correctly'})
    else:
        form = LoginForm()

    return render(request,'login.html')


# Check if the current session is valid
def check_validation(request):
    if request.COOKIES.get('session_token'):
        session = SessionToken.objects.filter(session_token=request.COOKIES.get('session_token')).first()
        if session:
            return session.user
    else:
        return None

# The view user has after logging in
# def feed(request):
#     return render(request,'feed.html')


# Post View
# def post_view(request):
def feed(request):
    user = check_validation(request)

    if user:
        if request.method == 'GET':
            form = PostForm()
            return render (request, 'feed.html', {'form': form})
        elif request.method == 'POST':
            form = PostForm(request.POST, request.FILES)

            if form.is_valid():
                image = form.cleaned_data.get('image')
                caption = form.cleaned_data.get('caption')
                # print 'Image saved in the db'
                # print os.path.join(BASE_DIR,post.image.url)



                post = PostModel(user=user, image=image, caption=caption)
                post.save()

                path = os.path.join(BASE_DIR,post.image.url)

                uploaded = cloudinary.uploader.upload(path)
                print uploaded['secure_url']

                post.image_url = uploaded['secure_url']
                post.save()

                return render(request,'feed_new.html',{'post': post})
        else:
            return redirect('/login/')
    else:
        # If the user is not logged in
        return redirect('/login/')

# Main feed View
def feed_main(request):
    # Validates if the user is logged in or not
    user = check_validation(request)

    if user:
        # posts = PostModel.objects.all().order_by('created_on')
        posts = PostModel.objects.all().order_by('-created_on')

        for post in posts:
            existing_like = LikeModel.objects.filter(post_id=post.id, user=user).first()
            if existing_like:
                post.has_liked = True


        return render(request,'feed_main.html',{'posts': posts})
    else:
        return redirect('/login/')

# Like view
def like(request):
    user = check_validation(request)
    if user and request.method=='POST':
        form = LikeForm(request.POST)

        if form.is_valid():
            post_id = form.cleaned_data.get('post').id
            existing_like = LikeModel.objects.filter(post_id=post_id, user=user).first()

            # If user has already registered a like, then delete it
            if existing_like:
                existing_like.delete()
            else:
                # Otherwise create a like
                post = LikeModel.objects.create(post_id=post_id, user=user)

                # Send email if the one who liked was someone other than the
                # one who posted the comment
                if post.user.email != post.post.user.email:
                    send_mail(
                        'Heyy, You got a like from '+post.user.name,
                        'Check it out at smartp2pmarketplace.com',
                        'smartp2pmarketplace.com',
                        [post.post.user.email],
                        fail_silently=False,
                        )

            return redirect('/feed/')
    else:
        return redirect('/login/')

# Comment View
def comment(request):
    user = check_validation(request)

    if user and request.method=='POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            post_id = form.cleaned_data.get('post').id
            comment_text = form.cleaned_data.get('comment_text')

            # Create a CommentModel object and save it in the database
            comment = CommentModel.objects.create(user=user, post_id=post_id, comment_text=comment_text)
            comment.save()

            # Send email if the one who liked was someone other than the
            # one who posted the comment
            if comment.user.email != comment.post.user.email:
                send_mail(
                    'Heyy, You got a comment from '+comment.user.name,
                    'Check it out at smartp2pmarketplace.com',
                    'smartp2pmarketplace.com',
                    [comment.post.user.email],
                    fail_silently=False,
                    )

            return redirect('/feed')
        else:
            return redirect('/feed/')
    else:
        return redirect('/login')
