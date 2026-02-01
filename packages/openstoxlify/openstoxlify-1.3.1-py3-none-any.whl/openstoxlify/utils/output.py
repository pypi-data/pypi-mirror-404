import json

from utcnow import utcnow

from ..models.output import Output, PlotOut, QuoteOut, QuotesOut, StrategyOut
from ..context import Context
from ..models.enum import PlotType

from .period import find_range_interval


def build_plots(ctx: Context, plot_type: PlotType):
    return [
        PlotOut(
            label=plot.label,
            data=[item.to_dict() for item in plot.data],
            screen_index=plot.screen_index,
        )
        for plot in ctx.plots().get(plot_type.value, [])
    ]


def output(ctx: Context):
    quotes = QuotesOut(
        ticker=ctx.symbol(),
        interval=find_range_interval(ctx.period()).interval,
        provider=ctx.provider().source(),
        data=[
            QuoteOut(
                timestamp=utcnow.get(q.timestamp.isoformat()),
                open=q.open,
                high=q.high,
                low=q.low,
                close=q.close,
                volume=q.volume,
            )
            for q in ctx.quotes()
        ],
    )

    out = Output(
        histogram=build_plots(ctx, PlotType.HISTOGRAM),
        line=build_plots(ctx, PlotType.LINE),
        area=build_plots(ctx, PlotType.AREA),
        strategy=[
            StrategyOut(
                label="default",
                data=[item.to_dict() for item in ctx.signals()],
            )
        ],
        quotes=quotes,
    )

    print(json.dumps(out.to_dict()))
