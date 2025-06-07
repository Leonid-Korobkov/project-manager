from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth import login
from django.http import JsonResponse
from .models import Project, Task
from .forms import UserRegistrationForm, ProjectForm, TaskForm
import json


def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация успешна! Добро пожаловать!')
            return redirect('projects:project_list')
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})


class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'
    
    def get_queryset(self):
        return (Project.objects.filter(team=self.request.user) | 
                Project.objects.filter(manager=self.request.user)).distinct()


class ProjectDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Project
    template_name = 'projects/project_detail.html'
    
    def test_func(self):
        project = self.get_object()
        return self.request.user == project.manager or self.request.user in project.team.all()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tasks'] = self.object.tasks.all()
        return context


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'
    success_url = reverse_lazy('projects:project_list')
    
    def form_valid(self, form):
        form.instance.manager = self.request.user
        messages.success(self.request, 'Проект успешно создан!')
        return super().form_valid(form)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


class ProjectUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'
    
    def test_func(self):
        project = self.get_object()
        return self.request.user == project.manager
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Проект успешно обновлен!')
        return super().form_valid(form)


class ProjectDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Project
    template_name = 'projects/project_confirm_delete.html'
    success_url = reverse_lazy('projects:project_list')
    
    def test_func(self):
        project = self.get_object()
        return self.request.user == project.manager
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Проект успешно удален!')
        return super().delete(request, *args, **kwargs)


@login_required
def task_create(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.user != project.manager and request.user not in project.team.all():
        messages.error(request, 'У вас нет прав для создания задач в этом проекте!')
        return redirect('projects:project_detail', pk=project_id)
    
    if request.method == 'POST':
        form = TaskForm(request.POST, project=project)
        if form.is_valid():
            task = form.save(commit=False)
            task.project = project
            task.created_by = request.user
            task.save()
            messages.success(request, 'Задача успешно создана!')
            return redirect('projects:project_detail', pk=project_id)
    else:
        form = TaskForm(project=project)
    
    return render(request, 'projects/task_form.html', {
        'form': form,
        'project': project,
        'title': 'Создание задачи'
    })


@login_required
def task_update(request, pk):
    task = get_object_or_404(Task, id=pk)
    project = task.project
    
    if request.user != project.manager and request.user != task.assigned_to:
        messages.error(request, 'У вас нет прав для редактирования этой задачи!')
        return redirect('projects:project_detail', pk=project.id)
    
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task, project=project)
        if form.is_valid():
            form.save()
            messages.success(request, 'Задача успешно обновлена!')
            return redirect('projects:project_detail', pk=project.id)
    else:
        form = TaskForm(instance=task, project=project)
    
    return render(request, 'projects/task_form.html', {
        'form': form,
        'project': project,
        'task': task,
        'title': 'Редактирование задачи'
    })


@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, id=pk)
    project = task.project
    
    if request.user != project.manager and request.user != task.created_by:
        messages.error(request, 'У вас нет прав для удаления этой задачи!')
        return redirect('projects:project_detail', pk=project.id)
    
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Задача успешно удалена!')
        return redirect('projects:project_detail', pk=project.id)
    
    return render(request, 'projects/task_confirm_delete.html', {
        'task': task,
        'project': project
    })


@login_required
def task_update_status(request, pk):
    task = get_object_or_404(Task, id=pk)
    project = task.project
    
    if request.user != project.manager and request.user != task.assigned_to:
        return JsonResponse({'success': False, 'error': 'У вас нет прав для обновления статуса этой задачи!'})
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_status = data.get('status')
            
            if new_status not in ['in_progress', 'completed']:
                return JsonResponse({'success': False, 'error': 'Неверный статус задачи!'})
            
            task.status = new_status
            task.save()
            
            return JsonResponse({'success': True})
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Неверный формат данных!'})
    
    return JsonResponse({'success': False, 'error': 'Метод не поддерживается!'})
