# krx_hj3415/cli.py
from __future__ import annotations

import asyncio
import typer

from db2_hj3415.mongo import mongo_from_env
from db2_hj3415.settings import get_settings
from db2_hj3415.universe.repo import ensure_indexes as ensure_indexes_universe
from db2_hj3415.nfs.repo import ensure_indexes as ensure_indexes_nfs

from krx_hj3415.usecases.sync_universe import run_sync, apply_removed

app = typer.Typer(no_args_is_help=True)


@app.callback()
def main() -> None:
    """
    KRX universe tools.
    (서브커맨드 그룹 고정용 callback)
    """
    pass


async def _maybe_await_close(mongo: object) -> None:
    close = getattr(mongo, "close", None)
    if close is None:
        return
    out = close()
    if asyncio.iscoroutine(out):
        await out


async def _mongo_bootstrap(db) -> None:
    s = get_settings()
    await ensure_indexes_universe(db, snapshot_ttl_days=s.SNAPSHOT_TTL_DAYS)
    await ensure_indexes_nfs(db, snapshot_ttl_days=s.SNAPSHOT_TTL_DAYS)


@app.command()
def sync(
    universe: str = typer.Argument("krx300", help="유니버스 이름 (현재: krx300)"),
    apply: bool = typer.Option(False, "--apply", help="removed를 nfs에서 실제 삭제까지 적용"),
    snapshot: bool = typer.Option(True, "--snapshot/--no-snapshot", help="universe snapshot 저장 여부"),
    max_days: int = typer.Option(15, "--max-days", help="최대 며칠 전까지 유효 엑셀 URL 탐색"),
):
    """
    1) 외부에서 유니버스 수집
    2) DB latest와 diff
    3) universe latest(+snapshot) 저장
    4) (옵션) removed codes를 nfs에서 삭제 적용
    """

    async def _run():
        mongo = mongo_from_env()
        db = mongo.get_db()
        try:
            await _mongo_bootstrap(db)

            d = await run_sync(db, universe=universe, max_days=max_days, snapshot=snapshot)

            typer.echo(f"\n=== UNIVERSE SYNC: {d.universe} ===")
            typer.echo(f"asof: {d.asof.isoformat()}")
            typer.echo(f"added: {len(d.added)}, removed: {len(d.removed)}, kept: {d.kept_count}")

            if d.added:
                typer.echo("\n[ADDED]")
                for it in d.added[:50]:
                    typer.echo(f"- {it.code} {it.name}")
                if len(d.added) > 50:
                    typer.echo(f"... ({len(d.added) - 50} more)")

            if d.removed:
                typer.echo("\n[REMOVED]")
                for it in d.removed[:50]:
                    typer.echo(f"- {it.code} {it.name}")
                if len(d.removed) > 50:
                    typer.echo(f"... ({len(d.removed) - 50} more)")

            if apply and d.removed:
                typer.echo("\n=== APPLY REMOVED TO NFS ===")
                r = await apply_removed(db, removed_codes=d.removed_codes)
                typer.echo(
                    f"latest_deleted={r.get('latest_deleted', 0)}, "
                    f"snapshots_deleted={r.get('snapshots_deleted', 0)}"
                )
            elif apply:
                typer.echo("\n(no removed codes) apply skipped")

        finally:
            await _maybe_await_close(mongo)

    asyncio.run(_run())


if __name__ == "__main__":
    app()