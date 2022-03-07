import os
import re
from datetime import datetime

from flask import Flask, render_template, request, abort
from sqlalchemy import Column, Integer, String, DateTime, Float, create_engine, select
from sqlalchemy.orm import declarative_base, Session
from sqlalchemy.pool import SingletonThreadPool

#
# -- Config.
#
DB_PATH = os.environ.get('CR_DB_PATH', default='test.db')
API_KEY = os.environ.get('CR_API_KEY', default='abc123')

#
# -- Flask.
#


app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def report():
    if request.method == 'POST':
        if not valid_report_form(request.form, request.remote_addr):
            return "Please fill in all fields except Note", 400
        persist_report(to_report(request.form, request.remote_addr))
        return render_template('report_saved.html')
    return render_template('report.html')


@app.route('/map', methods=['GET'])
def map():
    if request.args.get('key') != API_KEY: return abort(404)
    reports = sess.execute(select(Report).limit(100)).scalars().all()
    dict_reports = [dict(row) for row in sess.execute(Report.__table__.select()).all()]

    # Delete reports older than three days.
    sess.execute("DELETE FROM reports where julianday('now') - julianday(created_at) >= 3;")
    sess.commit()
    return render_template('map.html', reports=reports, dict_reports=dict_reports)


#
# -- Persistence.
#

engine = create_engine(f'sqlite:///{DB_PATH}', poolclass=SingletonThreadPool)
sess = Session(engine)
Base = declarative_base()


class Report(Base):
    __tablename__ = 'reports'

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, nullable=False)
    created_by = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    soldier_count = Column(Integer, nullable=False)
    tank_count = Column(Integer, nullable=False)
    truck_count = Column(Integer, nullable=False)
    distance_meters = Column(Integer, nullable=False)
    note = Column(String, nullable=False)
    phone = Column(String, nullable=False)


Base.metadata.create_all(engine)


def persist_report(report: Report):
    sess.add(report)
    sess.commit()


#
# -- Mapping.
#

def valid_report_form(form: dict, ip: str) -> bool:
    try:
        to_report(form, ip)
        return True
    except:
        return False


def to_report(form: dict, ip: str) -> Report:
    return Report(
        id=None,
        created_at=datetime.now(),
        created_by=ip,
        latitude=float_from(form, 'latitude'),
        longitude=float_from(form, 'longitude'),
        soldier_count=int_from(form, 'soldier_count'),
        tank_count=int_from(form, 'tank_count'),
        truck_count=int_from(form, 'truck_count'),
        distance_meters=int_from(form, 'distance_meters'),
        note=form['note'],
        phone=phone_from(form, 'phone')
    )


def float_from(form: dict, key: str) -> float:
    return float(form[key])


def int_from(form: dict, key: str) -> int:
    return int(form[key])


def phone_from(form: dict, key: str) -> str:
    if not re.fullmatch('0[0-9]{9}', form[key]): raise ValueError('No bueno numberino.')
    return form[key]


if __name__ == '__main__':
    app.run()
