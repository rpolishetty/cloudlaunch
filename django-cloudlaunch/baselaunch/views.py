from abc import ABCMeta, abstractmethod

from django.http.response import Http404
from rest_framework import mixins
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from baselaunch import models
from baselaunch import serializers
from baselaunch import view_helpers


class CustomNonModelObjectMixin(object):
    """
    A custom viewset mixin to make it easier to work with non-django-model viewsets.
    Only the list_objects() and retrieve_object() methods need to be implemented.
    Create and update methods will work normally through DRF's serializers.
    """
    __metaclass__ = ABCMeta

    def get_queryset(self):
        return self.list_objects()

    def get_object(self):
        obj = self.retrieve_object()
        if obj is None:
            raise Http404

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)
        return obj

    @abstractmethod
    def list_objects(self):
        """
        Override this method to return the list of objects for
        list() methods.
        """
        pass

    @abstractmethod
    def retrieve_object(self):
        """
        Override this method to return the object for the get method.
        If the returned object is None, an HTTP404 will be raised.
        """
        pass


class CustomModelViewSet(CustomNonModelObjectMixin, viewsets.ModelViewSet):
    pass


class CustomReadOnlyModelViewSet(CustomNonModelObjectMixin,
                                 viewsets.ReadOnlyModelViewSet):
    pass


class CustomReadOnlySingleViewSet(CustomNonModelObjectMixin,
                                  mixins.ListModelMixin,
                                  viewsets.GenericViewSet):

    def list(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def get_object(self):
        # return an empty data row so that the serializer can emit fields
        return {}


class ApplicationViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows applications to be viewed or edited.
    """
    queryset = models.Application.objects.all()
    serializer_class = serializers.ApplicationSerializer


class InfrastructureView(APIView):
    """
    List kinds in infrastructures.
    """

    def get(self, request, format=None):
        # We only support cloud infrastructures for the time being
        response = {'url': request.build_absolute_uri('clouds')}
        return Response(response)


class AuthView(APIView):
    """
    List authentication endpoints.
    """

    def get(self, request, format=None):
        data = {'login': request.build_absolute_uri(reverse('rest_auth:rest_login')),
                'logout': request.build_absolute_uri(reverse('rest_auth:rest_logout')),
                'user': request.build_absolute_uri(reverse('rest_auth:rest_user_details')),
                'registration': request.build_absolute_uri(reverse('rest_auth_reg:rest_register')),
                'password/reset': request.build_absolute_uri(reverse('rest_auth:rest_password_reset')),
                'password/reset/confirm': request.build_absolute_uri(reverse('rest_auth:rest_password_reset_confirm')),
                'password/reset/change': request.build_absolute_uri(reverse('rest_auth:rest_password_change')),
                }
        return Response(data)


class CloudViewSet(viewsets.ModelViewSet):
    """
    API endpoint to view and or edit cloud infrastructure info.
    """
    queryset = models.Cloud.objects.all()
    serializer_class = serializers.CloudSerializer


class ComputeViewSet(CustomReadOnlySingleViewSet):
    """
    List compute related urls.
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.ComputeSerializer


class RegionViewSet(CustomReadOnlyModelViewSet):
    """
    List regions in a given cloud.
    """
    permission_classes = (IsAuthenticated,)
    # Required for the Browsable API renderer to have a nice form.
    serializer_class = serializers.RegionSerializer

    def list_objects(self):
        provider = view_helpers.get_cloud_provider(self)
        return provider.compute.regions.list()

    def get_object(self):
        provider = view_helpers.get_cloud_provider(self)
        obj = provider.compute.regions.get(self.kwargs["pk"])
        return obj


class MachineImageViewSet(CustomModelViewSet):
    """
    List machine images in a given cloud.
    """
    permission_classes = (IsAuthenticated,)
    # Required for the Browsable API renderer to have a nice form.
    serializer_class = serializers.MachineImageSerializer

    def list_objects(self):
        provider = view_helpers.get_cloud_provider(self)
        return provider.compute.images.list()

    def get_object(self):
        provider = view_helpers.get_cloud_provider(self)
        obj = provider.compute.images.get(self.kwargs["pk"])
        return obj


class ZoneViewSet(CustomReadOnlyModelViewSet):
    """
    List zones in a given cloud.
    """
    permission_classes = (IsAuthenticated,)
    # Required for the Browsable API renderer to have a nice form.
    serializer_class = serializers.ZoneSerializer

    def list_objects(self):
        provider = view_helpers.get_cloud_provider(self)
        region_pk = self.kwargs.get("region_pk")
        region = provider.compute.regions.get(region_pk)
        if region:
            return region.zones
        else:
            raise Http404

    def get_object(self):
        return next((s for s in self.list_objects()
                     if s.id == self.kwargs["pk"]), None)


class SecurityViewSet(CustomReadOnlySingleViewSet):
    """
    List security related urls.
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.SecuritySerializer


class KeyPairViewSet(CustomModelViewSet):
    """
    List key pairs in a given cloud.
    """
    permission_classes = (IsAuthenticated,)
    # Required for the Browsable API renderer to have a nice form.
    serializer_class = serializers.KeyPairSerializer

    def list_objects(self):
        provider = view_helpers.get_cloud_provider(self)
        return provider.security.key_pairs.list()

    def get_object(self):
        provider = view_helpers.get_cloud_provider(self)
        obj = provider.security.key_pairs.get(self.kwargs["pk"])
        return obj


class SecurityGroupViewSet(CustomModelViewSet):
    """
    List security groups in a given cloud.
    """
    permission_classes = (IsAuthenticated,)
    # Required for the Browsable API renderer to have a nice form.
    serializer_class = serializers.SecurityGroupSerializer

    def list_objects(self):
        provider = view_helpers.get_cloud_provider(self)
        return provider.security.security_groups.list()

    def get_object(self):
        provider = view_helpers.get_cloud_provider(self)
        obj = provider.security.security_groups.get(self.kwargs["pk"])
        return obj


class SecurityGroupRuleViewSet(CustomModelViewSet):
    """
    List security group rules in a given cloud.
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.SecurityGroupRuleSerializer

    def list_objects(self):
        provider = view_helpers.get_cloud_provider(self)
        sg_pk = self.kwargs.get("security_group_pk")
        sg = provider.security.security_groups.get(sg_pk)
        if sg:
            return sg.rules
        else:
            raise Http404

    def get_object(self):
        provider = view_helpers.get_cloud_provider(self)
        sg_pk = self.kwargs.get("security_group_pk")
        sg = provider.security.security_groups.get(sg_pk)
        if not sg:
            raise Http404
        else:
            pk = self.kwargs.get("pk")
            return provider.security.security_groups.rules.get(pk)


class NetworkViewSet(CustomModelViewSet):
    """
    List networks in a given cloud.
    """
    permission_classes = (IsAuthenticated,)
    # Required for the Browsable API renderer to have a nice form.
    serializer_class = serializers.NetworkSerializer

    def list_objects(self):
        provider = view_helpers.get_cloud_provider(self)
        return provider.network.list()

    def get_object(self):
        provider = view_helpers.get_cloud_provider(self)
        obj = provider.network.get(self.kwargs["pk"])
        return obj


class SubnetViewSet(CustomModelViewSet):
    """
    List networks in a given cloud.
    """
    permission_classes = (IsAuthenticated,)

    def list_objects(self):
        provider = view_helpers.get_cloud_provider(self)
        return provider.network.subnets.list(network=self.kwargs["network_pk"])

    def get_object(self):
        provider = view_helpers.get_cloud_provider(self)
        return provider.network.subnets.get(self.kwargs["pk"])

    def get_serializer_class(self):
        if self.request.method == 'PUT':
            return serializers.SubnetSerializerUpdate
        return serializers.SubnetSerializer


class InstanceTypeViewSet(CustomReadOnlyModelViewSet):
    """
    List compute instance types in a given cloud.
    """
    permission_classes = (IsAuthenticated,)
    # Required for the Browsable API renderer to have a nice form.
    serializer_class = serializers.InstanceTypeSerializer
    lookup_field = 'name'
    lookup_value_regex = '[^/]+'

    def list_objects(self):
        provider = view_helpers.get_cloud_provider(self)
        return provider.compute.instance_types.list()

    def get_object(self):
        provider = view_helpers.get_cloud_provider(self)
        name = self.kwargs.get('name')
        obj = provider.compute.instance_types.find(name=name)
        if obj:
            return obj[0]
        else:
            raise Http404


class InstanceViewSet(CustomModelViewSet):
    """
    List compute instances in a given cloud.
    """
    permission_classes = (IsAuthenticated,)
    # Required for the Browsable API renderer to have a nice form.
    serializer_class = serializers.InstanceSerializer

    def list_objects(self):
        provider = view_helpers.get_cloud_provider(self)
        return provider.compute.instances.list()

    def get_object(self):
        provider = view_helpers.get_cloud_provider(self)
        obj = provider.compute.instances.get(self.kwargs["pk"])
        return obj


class BlockStoreViewSet(CustomReadOnlySingleViewSet):
    """
    List blockstore urls.
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.BlockStoreSerializer


class VolumeViewSet(CustomModelViewSet):
    """
    List volumes in a given cloud.
    """
    permission_classes = (IsAuthenticated,)
    # Required for the Browsable API renderer to have a nice form.
    serializer_class = serializers.VolumeSerializer

    def list_objects(self):
        provider = view_helpers.get_cloud_provider(self)
        return provider.block_store.volumes.list()

    def get_object(self):
        provider = view_helpers.get_cloud_provider(self)
        obj = provider.block_store.volumes.get(self.kwargs["pk"])
        return obj


class SnapshotViewSet(CustomModelViewSet):
    """
    List snapshots in a given cloud.
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.SnapshotSerializer

    def list_objects(self):
        provider = view_helpers.get_cloud_provider(self)
        return provider.block_store.snapshots.list()

    def get_object(self):
        provider = view_helpers.get_cloud_provider(self)
        obj = provider.block_store.snapshots.get(self.kwargs["pk"])
        return obj


class ObjectStoreViewSet(CustomReadOnlySingleViewSet):
    """
    List compute related urls.
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.ObjectStoreSerializer


class BucketViewSet(CustomModelViewSet):
    """
    List buckets in a given cloud.
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.BucketSerializer

    def list_objects(self):
        provider = view_helpers.get_cloud_provider(self)
        return provider.object_store.list()

    def get_object(self):
        provider = view_helpers.get_cloud_provider(self)
        obj = provider.object_store.get(self.kwargs["pk"])
        return obj


class BucketObjectViewSet(CustomModelViewSet):
    """
    List objects in a given cloud bucket.
    """
    permission_classes = (IsAuthenticated,)
    # Required for the Browsable API renderer to have a nice form.
    serializer_class = serializers.BucketObjectSerializer

    def list_objects(self):
        provider = view_helpers.get_cloud_provider(self)
        bucket_pk = self.kwargs.get("bucket_pk")
        bucket = provider.object_store.get(bucket_pk)
        if bucket:
            return bucket.list()
        else:
            raise Http404

    def get_object(self):
        provider = view_helpers.get_cloud_provider(self)
        obj = provider.object_store.get(self.kwargs["pk"])
        return obj
