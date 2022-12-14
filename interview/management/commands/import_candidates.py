import csv
from django.core.management import BaseCommand
from interview.models import Candidate

# python manage,py imoprt_candidates --path xxx

class Command(BaseCommand):
    help = '从一个csv文件的内容中读候选人的列表，导入到数据库中'

    def add_arguments(self, parser):
        parser.add_argument('--path', type=str)

    def handle(self, *args, **kwargs):
        path = kwargs['path']
        with open(path, 'rt') as f:
            reader = csv.reader(f, dialect='excel',delimiter=',')
            for row in reader:
                # print(row[0])
                candidate = Candidate.objects.create(
                    username = row[0],
                    city = row[1],
                    phone = row[2],
                    bachelor_school = row[3],
                    major = row[4],
                    degree = row[5],
                    test_score_of_general_ability = row[6],
                    paper_score = row[7]

                )
                print(candidate)

