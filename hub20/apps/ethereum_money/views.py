from django.db.models import BooleanField, Case, Q, Value, When
from django.db.models.query import QuerySet
from django.http import Http404
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from eth_utils import is_address
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from . import models, serializers


class TokenFilter(filters.FilterSet):
    listed = filters.BooleanFilter(label="listed", method="filter_listed")
    native = filters.BooleanFilter(label="native", method="filter_native")
    stable_tokens = filters.BooleanFilter(label="stable", method="filter_stable_tokens")
    fiat = filters.CharFilter(label="fiat", method="filter_fiat")

    def token_search(self, queryset, name, value):
        q_name = Q(name__istartswith=value)
        q_symbol = Q(symbol__iexact=value)
        q_chain_name = Q(chain__name__icontains=value)
        return queryset.filter(q_name | q_symbol | q_chain_name)

    def filter_listed(self, queryset, name, value):
        return queryset.exclude(lists__isnull=value)

    def filter_native(self, queryset, name, value):
        filtered_qs = queryset.filter if value else queryset.exclude
        return filtered_qs(address=models.EthereumToken.NULL_ADDRESS)

    def filter_stable_tokens(self, queryset, name, value):
        return queryset.exclude(stable_pair__token__isnull=value)

    def filter_fiat(self, queryset, name, value):
        return queryset.filter(stable_pair__currency__iexact=value)

    class Meta:
        model = models.EthereumToken
        ordering_fields = ("symbol", "chain_id")
        fields = ("chain_id", "symbol", "address", "listed", "native", "stable_tokens", "fiat")


class TokenViewSet(GenericViewSet, ListModelMixin, RetrieveModelMixin):
    serializer_class = serializers.HyperlinkedEthereumTokenSerializer
    filterset_class = TokenFilter
    filter_backends = (
        OrderingFilter,
        SearchFilter,
        filters.DjangoFilterBackend,
    )
    page_size = 50
    search_fields = ("name", "=symbol", "chain__name")
    ordering_fields = ("symbol", "name", "chain_id")
    ordering = ("-is_native", "chain_id", "symbol")

    def get_queryset(self) -> QuerySet:
        return models.EthereumToken.objects.filter(chain__providers__is_active=True).annotate(
            is_native=Case(
                When(address=models.EthereumToken.NULL_ADDRESS, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        )

    def get_object(self):
        address = self.kwargs["address"]
        if not is_address(address):
            raise Http404(f"{address} is not a valid token address")

        return get_object_or_404(
            models.EthereumToken, chain_id=self.kwargs["chain_id"], address=address
        )

    @action(detail=True)
    def info(self, request, **kwargs):
        """
        Returns extra information that the hub operator has provided about this token.


        """
        token = self.get_object()
        serializer = serializers.TokenInfoSerializer(instance=token, context=dict(request=request))
        return Response(serializer.data)


class TokenListViewSet(GenericViewSet, ListModelMixin, RetrieveModelMixin):
    """
    Token lists (https://tokenlists.org) is community-led effort to
    curate lists of ERC20 tokens. Hub Operators can create their own
    token lists, and its users can choose freely which ones to use.
    """

    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.TokenListSerializer
    queryset = models.TokenList.objects.all()


class UserTokenListView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.UserTokenListSerializer

    def get(self, request):
        return Response(
            [
                reverse("tokenlist-detail", kwargs={"pk": tl.pk}, request=request)
                for tl in request.user.token_lists.all()
            ]
        )
