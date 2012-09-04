View = require './view'
template = require './templates/framedetail'
application = require('application')
markupImage = require './widgets/markupImage'

module.exports = class FrameDetailView extends View  
  template: template

  initialize: (frame)=>
    super()
    for k in application.settings.ui_metadata_keys
      if !frame.model.attributes.metadata[k]?
        frame.model.attributes.metadata[k] = ''
    @frame = frame.model
    $(window).resize => @updateScale()
  
  events:
    'click #toggleProcessing' : 'togglePro'
    'click .clickEdit'  : 'switchStaticMeta'
    'blur .clickEdit'  : 'switchInputMeta'
    'change .notes-field' : 'updateNotes'
    'dblclick #display-zoom': 'clickZoom'

  togglePro: =>
    $("#display canvas").toggle()
    
  getRenderData: =>
    data = {}
   
    if @model.get("features").length
      data.featuretypes = _.values(@model.get("features").groupBy (f) -> f.get("featuretype"))
    
    for k of @model.attributes
      data[k] = @model.attributes[k]
    data.disabled = application.settings.mongo.is_slave || false

    md = @frame.get('metadata')
    metadata = []
    for i in application.settings.ui_metadata_keys
      metadata.push {key:i,val:md[i]}
      
    data.metadata = metadata
<<<<<<< Updated upstream
    data.capturetime = new moment(parseInt @frame.get('capturetime')+'000').format("M/D/YYYY h:mm a")
    data
=======
    data.capturetime_epoch = new moment(parseInt(@frame.get("capturetime_epoch"))).format("M/D/YYYY h:mm a")
    return data
>>>>>>> Stashed changes

  updateMetaData: (self) =>  
    metadata = {}
    
    rows = @$el.find(".editableMeta tr")
    rows.each (id, obj) ->
      tds = $(obj).find('td')
      input = $(tds[0]).find('input')
      span = $(tds[0]).find('span')[0]
      metadata[$(span).html()] = input.attr('value')
    
    @model.save {metadata: metadata}

  updateNotes: (e) =>
    @model.save {notes:$(".notes-field").attr('value')}

  switchStaticMeta: (e) =>
    self = $(e.currentTarget)
    if self.find("input").length == 0
      $(self).html "<input type=\"text\" value=\"" + self.html() + "\">"
      self.find("input").focus()

  switchInputMeta: (e) =>
    target = $(e.currentTarget).parent().parent()
    @updateMetaData(target)
    
  clickZoom: (e) ->
    viewPort = $('#display-zoom')
    scale = $("#zoomer").data("orig-scale")
    fakeZoom = Number($("#zoomer").data("last-zoom"))
    
    fakeZoom += .2
    clickX = e.clientX - 300
    clickY = e.clientY - 48
    oldLeft = clickX - Number($("#display-zoom").css("left").replace("px", ""))
    oldTop = clickY - Number($("#display-zoom").css("top").replace("px", ""))
    oldWidth = viewPort.width()
    oldHeight = viewPort.height()
    newWidth = (@.model.attributes.width * fakeZoom)
    newHeight = (@.model.attributes.height * fakeZoom)
    newLeft = oldLeft / oldWidth * newWidth  
    newTop = oldTop / oldHeight * newHeight
    x = Number($("#display-zoom").css("left").replace("px", "")) - (newLeft - oldLeft)
    y = Number($("#display-zoom").css("top").replace("px", "")) - (newTop - oldTop)
    
    $("#zoomer").zoomify("option", {zoom: Math.floor((fakeZoom*100))/100, x: (-x) / newWidth, y: (-y)/ newHeight})
    $('#display').css("height", (@.model.attributes.height * scale))    
  
  zoom: (e, ui) ->
    scale = $("#zoomer").data("orig-scale")
    
    $('#display').css "height", @.model.attributes.height * scale
    $('#display-zoom').css
      'position': 'relative',
      'top': '-'+(@.model.attributes.height * ui.zoom * ui.y)+'px',
      'left': '-'+(@.model.attributes.width * ui.zoom * ui.x)+'px',
      'width': (@.model.attributes.width * ui.zoom)+'px',
      'height': (@.model.attributes.height * ui.zoom)+'px',
    
    if ui.zoom != Number($("#zoomer").data("last-zoom"))
      @imagePreview.renderProcessing()
    
    $("#zoomer").data("last-zoom", ui.zoom)    

  calculateScale: =>
    framewidth = @model.get("width")
    realwidth = $('#display').width()
    scale = realwidth / framewidth

    scale

  updateScale: =>
    scale = @calculateScale()
    
    unless scale is $("#zoomer").data("orig-scale")
      fullHeight = $(window).height() - 48
      ui = {zoom: $("#zoomer").data("last-zoom")}
      
      $('#display-zoom').css
        'position': 'relative',
        'width': (@.model.attributes.width * ui.zoom)+'px',
        'height': (@.model.attributes.height * ui.zoom)+'px',
      
      $('#display').css "height", @.model.attributes.height * scale
        
      $("#zoomer").data "orig-scale", scale
      $("#zoomer").zoomify "option",
        min: (scale.toFixed(2)) * 100,
        max: 400,
        height: (fullHeight / @model.get("height")) / scale,
        zoom: scale.toFixed(2),
  
  postRender: =>
    application.throbber.clear()
    
    scale = @calculateScale()
    scaleFixed = scale.toFixed(2)
    displayHeight = $(window).height() - 48;
    
    @imagePreview =  @addSubview "display-zoom", markupImage, "#display-zoom"
    @imagePreview.setModel @model
    
    $("#zoomer")
      .data("orig-scale", scale)
      .zoomify
        y: 25
        max: 400
        min: scaleFixed * 100
        zoom: scaleFixed
        realWidth: @model.get("width")
        realHeight: @model.get("height")
        image: @model.get('imgfile')
        height: (displayHeight / @model.get("height")) / scale
        update: (e, ui) =>
          @zoom(e, ui)
      
    @$el.find(".notes-field").autogrow()
    
    $("#display-zoom").draggable
      drag: (e, ui) ->
        w0 = $("#frameHolder").width()
        h0 = $("#frameHolder").height()
        w = $("#display-zoom").width()
        h = $("#display-zoom").height()
        
        if ui.position.left > 0 then ui.position.left = 0
        if ui.position.top > 0 then ui.position.top = 0
        if -1*ui.position.left + w0 > w then ui.position.left = w0 - w
        if -1*ui.position.top + h0 > h then ui.position.top = h0 - h

        $("#zoomer").zoomify("option", {"x": -1*ui.position.left / w, "y": -1*ui.position.top / h})
    
