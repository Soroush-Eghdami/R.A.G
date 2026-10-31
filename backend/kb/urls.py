from rest_framework.routers import DefaultRouter

from .views import DocumentViewSet, KnowledgeBaseViewSet

router = DefaultRouter()
router.register("knowledge-bases", KnowledgeBaseViewSet, basename="knowledgebase")
router.register("documents", DocumentViewSet, basename="document")

urlpatterns = router.urls
