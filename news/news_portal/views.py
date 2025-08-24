
from django.shortcuts import redirect, render, get_object_or_404
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView, TemplateView
from .models import Post, Category, PostCategory, Author
from .filters import PostFilter
from .forms import PostForm
from django.urls import reverse_lazy
from .forms import PostSearchForm
from django.contrib.auth.mixins import LoginRequiredMixin, LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.views import LogoutView
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required



class PostsList(ListView):
    model = Post
    ordering = '-creation_time'
    template_name = 'posts.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        self.filterset = PostFilter(self.request.GET, queryset)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filterset'] = self.filterset
        context['total_posts_count'] = self.filterset.qs.count()  # Общее количество после фильтрации
        return context

class PostDetail(DetailView): 
    model = Post
    template_name = 'post.html'
    context_object_name = 'post'

def create_post(request):
    form = PostForm()
    
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            form.save()

    return render(request, 'post_edit.html', {'form': form})

class PostUpdate(UpdateView):
    form_class = PostForm
    model = Post
    template_name = 'post_edit.html'

class PostDelete(DeleteView):
    model = Post
    template_name = 'post_delete.html'
    success_url = reverse_lazy('post_list')

class PostSearchView(ListView):
    model = Post
    template_name = 'news_search.html'
    context_object_name = 'news'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        form = PostSearchForm(self.request.GET)
        
        if form.is_valid():
            name = form.cleaned_data.get('name')
            author = form.cleaned_data.get('author')
            date_after = form.cleaned_data.get('date_after')
            
            if name:
                queryset = queryset.filter(name__icontains=name)
            
            if author:
                queryset = queryset.filter(author__username__icontains=author)
            
            if date_after:
                queryset = queryset.filter(creation_time__gte=date_after)
        
        return queryset.order_by('-creation_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = PostSearchForm(self.request.GET)
        return context

from django.db import transaction

class NewsCreate(PermissionRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'new_create.html'
    permission_required = 'news_portal.add_post'

    @transaction.atomic
    def form_valid(self, form):
        author = Author.objects.get(user=self.request.user)
        
        post = form.save(commit=False)
        post.article_or_news = 'NW'
        post.author = author
        post.save()
        
        categories = form.cleaned_data['categories']
        post.category.set(categories)
        
        return redirect(post.get_absolute_url())
    
    def get_success_url(self):
        return reverse_lazy('post_detail', kwargs={'pk': self.object.pk})

class NewsUpdate(PermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'new_create.html'
    permission_required = 'news_portal.change_post'
    success_url = reverse_lazy('post_list')
    
    def get_queryset(self):
        return super().get_queryset().filter(article_or_news='NW')

class NewsDelete(PermissionRequiredMixin, DeleteView):
    model = Post
    template_name = 'post_confirm_delete.html'
    permission_required = 'news_portal.delete_post'
    success_url = reverse_lazy('post_list')
    
    def get_queryset(self):
        return super().get_queryset().filter(article_or_news='NW')

class ArticleCreate(PermissionRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'new_create.html'
    permission_required = 'news_portal.add_post'

    @transaction.atomic
    def form_valid(self, form):
        author = Author.objects.get(user=self.request.user)
        
        post = form.save(commit=False)
        post.article_or_news = 'AR'
        post.author = author
        post.save()
        
        categories = form.cleaned_data['categories']
        post.category.set(categories)
        
        return redirect(post.get_absolute_url())
    def get_success_url(self):
        return reverse_lazy('post_detail', kwargs={'pk': self.object.pk})
    

class ArticleUpdate(PermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'article_create.html'
    permission_required = 'news_portal.change_post'
    success_url = reverse_lazy('post_list')
    
    def get_queryset(self):
        return super().get_queryset().filter(article_or_news='AR')

class ArticleDelete(PermissionRequiredMixin, DeleteView):

    model = Post
    template_name = 'post_confirm_delete.html'
    permission_required = 'news_portal.delete_post'
    success_url = reverse_lazy('post_list')
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Добавим отладочную информацию
        print(f"Все записи: {queryset.count()}")
        filtered = queryset.filter(article_or_news='AR')
        print(f"После фильтрации: {filtered.count()}")
        return filtered
    

class CLogoutView(LogoutView):
    template_name = 'logout_user.html'
    next_page = reverse_lazy('post_list')



class IndexView(LoginRequiredMixin, TemplateView):
    template_name = 'personal_account.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_not_author'] = not self.request.user.groups.filter(name = 'author').exists()
        return context
    

@login_required
def upgrade_me(request):
    user = request.user
    author_group = Group.objects.get(name='author')
    if not request.user.groups.filter(name='author').exists():
        author_group.user_set.add(user)
    return redirect('/posts/personal')

@login_required
def subscribe(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.user in category.subscribers.all():
        category.subscribers.remove(request.user)
    else:
        category.subscribers.add(request.user)
    return redirect('post_list')