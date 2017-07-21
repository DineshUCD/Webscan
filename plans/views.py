from django.shortcuts import render, reverse, get_object_or_404
from django.http import HttpResponse,HttpResponseRedirect,JsonResponse
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory
from django.db import IntegrityError, transaction

from accounts.Group import Guardian
from scans.models import Tool
from .models import Plan
from .forms import PlanForm


# Create your views here.
def my_plans(request, template_name='plans/index.html'):
    guardian = Guardian()

    context = {
        'plans': Plan.objects.filter(user_profile__id=int(request.user.userprofile.id), scan=None),
        'group_objects' : dict(guardian.order_by_object(request.user))
    }

    return render(request, template_name, context)
 
class PlanCreate(CreateView):
    form_class = PlanForm
    template_name = 'plans/edit_plan.html'
    success_url = reverse_lazy('plans:plans-list')

    def get_form_kwargs(self):
        kwargs = super(PlanCreate, self).get_form_kwargs()
        if 'data' in kwargs:
            print kwargs['data']
            if 'form-0-configuration' in kwargs['data']:
                print kwargs['data']['form-0-configuration']
            if 'form-NaN-configuration' in kwargs['data']:
                print kwargs['data']['form-NaN-configuration']
        print "POST"
        print self.request.POST
        if self.request.POST:
            CliFormSet = modelformset_factory(Tool, fields=('configuration',))
            formset = CliFormSet(self.request.POST)
            instances = formset.save(commit=False)
            for instance in instances:
              print instance.configuration
            print instances
        kwargs['user_profile_id'] = self.request.user.userprofile.id
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super(PlanCreate, self).get_context_data(**kwargs)
        context['action']   = reverse('plans:plans-new')
        CliFormSet = modelformset_factory(Tool, fields=('configuration', ))
        context['cliForms'] = CliFormSet(queryset=Tool.objects.none())
        return context

class PlanUpdate(UpdateView):
    form_class = PlanForm
    template_name = 'plans/edit_plan.html'
    success_url = reverse_lazy('plans:plans-list')
     
    def get_form(self):
        form  = super(PlanUpdate, self).get_form()
        tools = [ tool.module for tool in self.get_object().tool_set.all() ]
        form.initial['plugins'] = tools
        return form
   
    def get_context_data(self, **kwargs):
        context = super(PlanUpdate, self).get_context_data(**kwargs)
        context['action'] = reverse('plans:plans-edit', kwargs={'pk': self.get_object().id}) 
        return context
    
    def get_object(self, queryset=None):
        obj = get_object_or_404(Plan, user_profile__id=self.request.user.userprofile.id, pk=int(self.kwargs['pk']))
        return obj
    
class PlanDelete(DeleteView):
    model = Plan
    template_name = 'plans/index.html'
    success_url   = reverse_lazy('plans:plans-list')
   
    def get_object(self, queryset=None):
        obj = get_object_or_404(Plan, user_profile__id=self.request.user.userprofile.id, pk=int(self.kwargs['pk']))
        return obj

@login_required(login_url='/accounts/login')
def select(request, pk):
    user_profile = request.user.userprofile
    user_session = user_profile.get_current()
 
    guardian = Guardian()
    plan     = guardian.verify_by_contenttype('plan', request.user, pk)

    if not plan:
        plan = get_object_or_404(Plan, user_profile__id=int(user_profile.id), pk=pk)

    if request.method == 'POST':
        if 'add' in request.POST:
            user_session.set_session(user_session.appenditem  , plan=plan.id) 
        elif 'remove' in request.POST:
            user_session.set_session(user_session.unappenditem, plan=plan.id)  
    return HttpResponseRedirect(reverse('plans:plans-list'))
