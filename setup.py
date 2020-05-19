from setuptools import setup

setup(
   name='es_bank_accounts',
   version='0.1.0',
   description='Eventsourced example for a bankaccount system',
   install_requires=[
        "eventsourcing == 8.2.1",
        "fastapi == 0.53.2",
        "uvicorn == 0.11.3"
   ],
)