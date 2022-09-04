from django.contrib import admin
from interview.models import Candidate
# Register your models here.
from django.http import HttpResponse
from django.db.models import Q
import csv 
from datetime import datetime 
from interview import candidate_field as cf
from interview import dingtalk
import logging
logger = logging.getLogger(__name__)
exportable_fileds = ('username', 'city', 'phone')

# 通知一面面试官面试
def notify_interviewer(modeladmin, request, queryset):
    candidates = ""
    interviewers = ""
    for obj in queryset:
        candidates = obj.username + ";" + candidates
        interviewers = obj.first_interviewer_user.username + ";" + interviewers
    # 这里的消息发送到钉钉， 或者通过 Celery 异步发送到钉钉
    dingtalk.send("候选人 %s 进入面试环节，亲爱的面试官，请准备好面试： %s" % (candidates, interviewers) )
    # send_dingtalk_message.delay("候选人 %s 进入面试环节，亲爱的面试官，请准备好面试： %s" % (candidates, interviewers) )
    # messages.add_message(request, messages.INFO, '已经成功发送面试通知')


notify_interviewer.short_description = u'通知一面面试官'

def export_model_as_csv(modeladmin, request, queryset):
    """需要将【导出为csv】 添加到 应聘者admin的action中"""
    response = HttpResponse(content_type="text/csv")
    field_list = exportable_fileds
    response['Content-Disposition'] = 'attachment; filename=recruitment-candidates-list-%s.csv' % (
        datetime.now().strftime('%Y-%m-%d_%H-%M-%s'),

    )
    # 写入表头 
    writer = csv.writer(response)
    writer.writerow(
        [ queryset.model._meta.get_field(f).verbose_name.title() for f in field_list]
    )
    
    for obj in queryset:
        csv_line_values = []
        for field in field_list:
            field_object = queryset.model._meta.get_field(field)
            field_value = field_object.value_from_object(obj)
            csv_line_values.append(field_value)
        writer.writerow(csv_line_values)   
    logger.info("%s exported %s candidate records" % (request.user, len(queryset)))
    return response
    
export_model_as_csv.short_description = '导出为csv文件'
export_model_as_csv.allowd_permissions = ('export',)

# 定义在admin展示哪些内容
class CandidateAdmin(admin.ModelAdmin):
    """候选人管理类，"""
    # 将【导出为csv】 添加到 应聘者admin的action中
    actions = [export_model_as_csv, notify_interviewer,]

    ## 当前用户是否有导出权限
    def has_export_permission(self, request):
        opts = self.opts
        return request.user.has_perm('%s.%s'% (opts.app_label, "export"))

    # 隐藏字段
    exclude = ('creator', 'created_date', 'modified_date')
    # 展示字段
    list_display = (
        'username', 'city', 'bachelor_school', 'first_score', 'first_result', 'first_interviewer_user',
        'second_result', 'second_interviewer_user', 'hr_score', 'hr_result', 'last_editor'
    )
    # 用于查询的字段
    search_fields = ('username', 'phone', 'email', 'bachelor_school')

    # 用于筛选的字段
    list_filter = ('city', 'first_result', 'second_result', 'hr_result', 'first_interviewer_user', 'second_interviewer_user', 'hr_interviewer_user')
    
    # 让面试官账号无法修改面试官
    def get_group_names(self, user):
        group_names = []
        for g in user.groups.all():
            group_names.append(g.name)
        return group_names

    def get_readonly_fields(self, request, obj):
        group_names = self.get_group_names(request.user)
        if 'interviewer' in group_names:
            logger.info("interviewer is in user's group for %s" % request.user.username)
            return ('first_interviewer_user', 'second_interviewer_user')
        return ()  

    # 一面面试官仅填写一面反馈， 二面面试官可以填写二面反馈
    def get_fieldsets(self, request, obj=None):
        group_names = self.get_group_names(request.user)

        if 'interviewer' in group_names and obj.first_interviewer_user == request.user:
            return cf.default_fieldsets_first
        if 'interviewer' in group_names and obj.second_interviewer_user == request.user:
            return cf.default_fieldsets_second
        return cf.default_fieldsets
    # 对于非管理员，非HR，获取自己是一面或二面的候选人集合:s
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        group_names = self.get_group_names(request.user)
        if request.user.is_superuser or 'hr' in group_names:
            return qs 
        return Candidate.objects.filter(
            Q(first_interviewer_user=request.user) | Q(second_interviewer_user=request.user)
        )            
    # 定义哪些字段可以直接编辑
    # default_list_editable = ('first_interviewer_user', 'second_interviewer_user')
    # def get_list_editable(self, request):
    #     group_names = self.get_group_names(request)
    #     if request.user.is_superuser or 'hr' in group_names:
    #         return self.default_list_editable
    #     return ()            
    # def get_changelist_instance(self, request):
    #     self.list_editable = self.get_list_editable(request)
    #     return super().get_changelist_instance(request)

 
admin.site.register(Candidate, CandidateAdmin)