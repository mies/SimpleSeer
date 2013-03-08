[Template, SubView] = [
	require('views/widgets/templates/imagecanvas'),
	require('views/core/subview')
]

# ImageCanvas provides a image and 
# a canvas bound to a Processing.js
# object. This widget handles dirty
# tasks like handling scale.

module.exports = class ImageCanvas extends SubView
	template: Template
	canvas: {}
	image: {}
	processing: {}
	_scaleFactor: 1

	getRenderData: =>
		image: @options.image

	afterRender: =>
		@canvas = @$("canvas")
		@image = @$("img")
		@image.load =>
			@image.show()
			@_scale()
			@_align()
			@_markup(@options.engine)

	# The padding method is called when
	# the widget is given a padding option.
	# Padding is used to push the image 
	# away from the edges of the canvas to
	# prevent any clipping of the markup.
	_align: =>
		[w, h] = [@image.width(), @image.height()]
		left = (@options.width - w) / 2
		top = (@options.height - h) / 2

		@image.css
			"left": "#{left}px"
			"top": "#{top}px"

	# The scale method is called when
	# the canvas and image need to be
	# sized to the parent container.
	_scale: =>
		[w, h] = [@image.width(), @image.height()]
		box =
			width: @options.width - @options.padding * 2,
			height: @options.height - @options.padding * 2
		
		# Check if we need to scale down the image itself.
		wider = (w > box.width)
		taller = (h > box.height)
		console.log w, h, box
		if(wider or taller)
			if (w - box.width > h - box.height)
				@_scaleFactor = box.width / w
			else
				@_scaleFactor = box.height / h
			@image.width(w * @_scaleFactor)
			@image.height(h * @_scaleFactor)			

	# The markup method is called each
	# time the view is rendered. It draws
	# on the canvas. No drawing is done by
	# default.
	_markup:(engine = =>) =>
		[w, h] = [@canvas.width(), @canvas.height()]
		@processing = new Processing(@canvas.get(0))
		@processing.size w, h
		#@processing.scale @_scaleFactor
		@processing.background 0, 0
		engine(@processing, @options)
