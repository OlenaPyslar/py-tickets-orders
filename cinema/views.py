from django.db.models import Count, F, Q
from django.utils.dateparse import parse_date
from django.utils.datetime_safe import datetime
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request

from cinema.models import (
    Genre, Actor, CinemaHall,
    Movie, MovieSession, Order, Ticket)

from cinema.serializers import (
    GenreSerializer,
    ActorSerializer,
    CinemaHallSerializer,
    MovieSerializer,
    MovieSessionSerializer,
    MovieSessionListSerializer,
    MovieDetailSerializer,
    MovieSessionDetailSerializer,
    MovieListSerializer, OrderSerializer, TicketSerializer,
)


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer


class CinemaHallViewSet(viewsets.ModelViewSet):
    queryset = CinemaHall.objects.all()
    serializer_class = CinemaHallSerializer


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def get_queryset(self):
        queryset = Movie.objects.all()

        title = self.request.query_params.get("title")
        genres = self.request.query_params.get("genres")
        actors = self.request.query_params.get("actors")

        if title:
            queryset = queryset.filter(
                title__icontains=title
            )

        if genres:
            genres_ids = [
                int(id_) for id_ in genres.split(",") if id_.isdigit()
            ]
            queryset = queryset.filter(
                genres__id__in=genres_ids
            )

        if actors:
            actors_ids = [
                int(id_) for id_ in actors.split(",") if id_.isdigit()
            ]
            queryset = queryset.filter(
                actors__id__in=actors_ids
            ).distinct()

        return queryset


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()
    serializer_class = MovieSessionSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    def get_queryset(self):
        queryset = MovieSession.objects.all()

        date = self.request.query_params.get("date")
        movie = self.request.query_params.get("movie")

        if date:
            date_obj = parse_date(date)
            if date_obj:
                queryset = queryset.filter(show_time__date=date_obj)

        if movie:
            queryset = queryset.filter(movie_id=movie)

        if self.action == "list":
            queryset = (
                queryset
                .select_related()
                .annotate(
                    tickets_available=(F("cinema_hall__rows") * F("cinema_hall__seats_in_row") - Count("tickets"))
                )
            )

        return queryset


class OrderPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
