import datetime as dt


def year(request):
    """Добавляет переменную с текущим годом."""
    date = dt.datetime.now().year
    return {
        'year': date
    }
