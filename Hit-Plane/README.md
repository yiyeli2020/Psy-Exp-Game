# Hit-a-Plane
bullet.py 子弹  <br />
enmey.py 敌人  <br />
myplane.py 飞机<br />
supply.py 补及<br />

part1思路：<br />
写main()<br />
1.先导入需要用到的pygame、sys、traceback模块<br />
 from pygame.locals import * 这个是导入常用函数与常量。<br />
2.初始化pygame，pygame.mixer<br />
3.设置分辨率与背景图<br />
4.导入音效资源<br />
 pygame.mixer.music.load（）<br />
 bomb_sound = pygame.mixer.Sound（）<br />
5.写main（），播放音乐，用for循环获取时间与绘制背景图<br />
6、if __name__ == '__main__':<br />
	try:<br />
		main()<br />
	except SystemExit:<br />
		pass<br />
	except:<br />
		traceback.print_exc()<br />
		pygame.quit()<br />
		input()<br />

part2：<br />
优化：<br />
1.结束游戏是隐藏暂停按钮<br />
定义一个BUTTON_ON = True<br />
BUTTON_ON为True是绘制按钮<br />
结束游戏时把BUTTON_ON = False<br />

说明：进入游戏，即可开始。每个trial根据难度控制在45s以内，初始trial的最开始难度可设置为0，trial内难度增加，增加难度的具体参数由编程者拟定，当被试达在单位时间内到一定分数时或者失败后，此trial结束，如果被试成功完成，则继续试验，否则出现是否重新试验界面。下一个trial难度由上一个trial决定，如果上一个trial成功，则下一个trial初始难度为上一个结束时难度的10%，再逐渐增加；如果上一个trial失败，则下一个trial难度退回到上个难度初始前难度10%。最后当被试共计成功完成15个trial后，退出游戏。


效果图：<br />
![Image text](https://github.com/afantishui/Hit-a-Plane/blob/master/playing.png)<br />
![Image text](https://github.com/afantishui/Hit-a-Plane/blob/master/gameover.png)<br />
