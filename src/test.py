def add_button_to_grid (self, grid, stock, x, y, tooltip):
		#if not self.save_button:
		button = Gtk.Button.new()
		image = Gtk.Image()
		image.set_from_stock(stock,4)
		button.set_alignment(0.0, 0.0)
		button.set_tooltip_text(tooltip)
		button.add(image)