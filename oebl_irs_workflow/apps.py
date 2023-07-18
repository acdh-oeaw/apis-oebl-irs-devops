from django.apps import AppConfig


class ApisIRSWorkflowConfig(AppConfig):
    name = 'oebl_irs_workflow'
    def ready(self):
        import oebl_irs_workflow.signals
