from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum
from django.urls import reverse


class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    subscribers = models.ManyToManyField(User, related_name='subscribed_categories', blank=True)

    def __str__(self):
        return f'{self.name}'

class Author(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    rating=models.IntegerField(default=0)
    def __str__(self):
        return f'{self.user.username}'
    
    def update_rating(self):
        article_rating = self.post_set.aggregate(
        total_article_rating=Sum('rating') * 3
        )['total_article_rating'] or 0
    
        # Суммарный рейтинг комментариев автора
        author_comments_rating = self.user.comment_set.aggregate(
        total_comment_rating=Sum('rating')
        )['total_comment_rating'] or 0
    
        # Суммарный рейтинг комментариев к статьям автора
        article_comments_rating = Comment.objects.filter(
        comment_post__author=self  # Изменено с post__author на comment_post__author
        ).aggregate(
        total_article_comments_rating=Sum('rating')
        )['total_article_comments_rating'] or 0
    
        self.rating = (
        article_rating + 
        author_comments_rating + 
        article_comments_rating
        )
        self.save()
        

class Post(models.Model):
    ARTICLE = 'AR'
    NEWS = 'NW'
    POST_TYPES = [
        (ARTICLE, 'Статья'),
        (NEWS, 'Новость'),
    ]

    article_or_news = models.CharField(max_length=2, choices=POST_TYPES)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)  
    creation_time=models.DateTimeField(auto_now_add=True)
    category = models.ManyToManyField(Category, through = 'PostCategory')
    name=models.CharField(max_length=255)
    text=models.TextField()
    rating=models.IntegerField(default=0)

    def __str__(self):
        return f'{self.name} | {self.author}'

    def get_absolute_url(self):
        return reverse('post_detail', args=[str(self.id)])

    def like(self):
        self.rating += 1
        self.save()

    def dislike(self):
        self.rating -= 1
        self.save()



class PostCategory(models.Model):
    post=models.ForeignKey(Post, on_delete=models.CASCADE)
    category=models.ForeignKey(Category, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('post', 'category')

    def __str__(self):
        return f'{self.category} | {self.post}'



class Comment(models.Model):
    comment_post=models.ForeignKey(Post, on_delete=models.CASCADE)
    comment_user=models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    date_upload=models.DateTimeField(auto_now_add=True)
    rating=models.IntegerField(default=0)

    def like(self):
        self.rating += 1
        self.save()

    def dislike(self):
        self.rating -= 1
        self.save()

    def __str__(self):
        return f'{self.comment_post} | {self.text}'