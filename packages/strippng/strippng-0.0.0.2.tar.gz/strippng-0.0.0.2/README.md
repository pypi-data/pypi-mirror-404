## python-strippng

Fast PNG stripper. (approx 20ms. Normal PIL.Image.imread/imwrite take approx 200ms as recompression is involved)

Though if not integrating to larger Python works, https://github.com/cielavenir/7bgzf/blob/master/applet/7png.c program is 10x faster (approx 2ms) (and better-recompression can be added on-demand).
