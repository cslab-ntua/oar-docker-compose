# coding: utf-8
import pytest

from oar.lib import Accounting, db
from oar.lib.accounting import (
    delete_accounting_windows_before,
    delete_all_from_accounting,
    get_accounting_summary,
    get_accounting_summary_byproject,
    get_last_project_karma,
)
from oar.lib.job_handling import insert_job

from ..helpers import insert_terminated_jobs


@pytest.fixture(scope="function", autouse=True)
def minimal_db_initialization(request):
    with db.session(ephemeral=True):
        # add some resources
        for i in range(10):
            db["Resource"].create(network_address="localhost")

        db["Queue"].create(name="default")
        yield


@pytest.mark.skipif(
    "os.environ.get('DB_TYPE', '') != 'postgresql'", reason="need postgresql database"
)
def test_check_accounting_update_one():
    insert_terminated_jobs(nb_jobs=1)
    accounting = db.query(Accounting).all()

    for a in accounting:
        print(
            a.user,
            a.project,
            a.consumption_type,
            a.queue_name,
            a.window_start,
            a.window_stop,
            a.consumption,
        )
    assert accounting[7].consumption == 172800


@pytest.mark.skipif(
    "os.environ.get('DB_TYPE', '') != 'postgresql'", reason="need postgresql database"
)
def test_check_accounting_update():
    insert_terminated_jobs()
    accounting = db.query(Accounting).all()
    for a in accounting:
        print(
            a.user,
            a.project,
            a.consumption_type,
            a.queue_name,
            a.window_start,
            a.window_stop,
            a.consumption,
        )

    assert accounting[7].consumption == 864000


@pytest.mark.skipif(
    "os.environ.get('DB_TYPE', '') != 'postgresql'", reason="need postgresql database"
)
def test_delete_all_from_accounting():
    insert_terminated_jobs()
    delete_all_from_accounting()
    accounting = db.query(Accounting).all()
    assert accounting == []


@pytest.mark.skipif(
    "os.environ.get('DB_TYPE', '') != 'postgresql'", reason="need postgresql database"
)
def test_delete_accounting_windows_before():
    insert_terminated_jobs()
    accounting1 = db.query(Accounting).all()
    delete_accounting_windows_before(5 * 86400)
    accounting2 = db.query(Accounting).all()
    assert len(accounting1) > len(accounting2)


def test_get_last_project_karma():
    user = "toto"
    project = "yopa"
    start_time = 10000
    karma = " Karma=0.345"
    insert_job(
        res=[(60, [("resource_id=2", "")])],
        properties="",
        command="yop",
        user=user,
        project=project,
        start_time=start_time,
        message=karma,
    )
    msg1 = get_last_project_karma("toto", "yopa", 50000)
    msg2 = get_last_project_karma("titi", "", 50000)
    assert karma == msg1
    assert "" == msg2


@pytest.mark.skipif(
    "os.environ.get('DB_TYPE', '') != 'postgresql'", reason="need postgresql database"
)
def test_get_accounting_summary():
    insert_terminated_jobs()
    result1 = get_accounting_summary(0, 100 * 86400)
    result2 = get_accounting_summary(0, 100 * 86400, "toto")
    print(result1)
    print(result2)
    assert result1["zozo"]["USED"] == 8640000
    assert result1["zozo"]["ASKED"] == 10368000
    assert result2 == {}


@pytest.mark.skipif(
    "os.environ.get('DB_TYPE', '') != 'postgresql'", reason="need postgresql database"
)
def test_get_accounting_summary_byproject():
    insert_terminated_jobs()
    result1 = get_accounting_summary_byproject(0, 100 * 86400)
    result2 = get_accounting_summary_byproject(0, 100 * 86400, "toto")
    print(result1)
    print(result2)
    assert result1["yopa"]["ASKED"]["zozo"] == 10368000
    assert result1["yopa"]["USED"]["zozo"] == 8640000
    assert result2 == {}
    assert True
