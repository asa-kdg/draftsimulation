from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

def rating_field(verbose_name):
    return models.DecimalField(
        verbose_name=verbose_name,
        max_digits=2,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(1.0),
            MaxValueValidator(5.0),
        ]
    )

class Team(models.Model):
    name = models.CharField(max_length=100)
    order = models.IntegerField() 
    first_color = models.CharField(max_length=7, default="#ffffff")
    second_color = models.CharField(max_length=7, default="#ffffff")


    def __str__(self):
        return self.name 

class Player(models.Model):
    CATEGORY_CHOICES = [
        ('HS', '高校生'),
        ('UNIV', '大学生'),
        ('IND', '独立・社会人'),
    ]

    POSITION_CHOICES =[
        ('P','投手'),
        ('C','捕手'),
        ('IF','内野手'),
        ('OF','外野手'),
    ]

    BATS_CHOICES =[
        ('R/R','右投右打'),
        ('R/L','右投左打'),
        ('R/B','右投両打'),
        ('L/R','左投右打'),
        ('L/L','左投左打'),
        ('L/B','左投両打'),
    ]

    name = models.CharField(max_length=100)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    position = models.CharField(max_length=5, choices=POSITION_CHOICES)
    team = models.CharField(max_length=100)
    bats_throws = models.CharField(max_length=10, choices=BATS_CHOICES)
    height = models.IntegerField()  # cm
    weight = models.IntegerField()  # kg
    introduction = models.TextField(blank=True, verbose_name='選手紹介')
    scout_comment = models.TextField(blank=True)
    drafted_team = models.ForeignKey(
        Team,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    

    def __str__(self):
        return self.name
    
class Comment(models.Model): 
    RANK_CHOICES =[
        ('S','S:1位指名候補'),
        ('A','A:上位指名候補'),
        ('B','B:中位指名候補'),
        ('C','C:下位指名候補'),
        ('D','D:育成指名候補'),
    ]
    
    player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    text = models.TextField('コメント')
    rank = models.CharField('評価', max_length=1, choices=RANK_CHOICES)
    velocity = rating_field('球威')
    command = rating_field('コントロール')
    breakingball = rating_field('変化球')
    mechanics = rating_field('フォーム')
    batcontroll = rating_field('ミート')
    power = rating_field('パワー')
    speed = rating_field('走塁')
    defense = rating_field('守備')
    potential = rating_field('将来性')
    created_at = models.DateTimeField(auto_now_add=True)
    

 




class Pick(models.Model):
    round = models.IntegerField()
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)










# Create your models here.
