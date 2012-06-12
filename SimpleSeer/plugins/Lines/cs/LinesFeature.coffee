class LineFeature
  constructor: (feature) ->
    @feature = feature
   
  icon: () => "/img/line.png" 
    
  represent: () =>  "Line Detected at (" + @feature.get("x") + ", " + @feature.get("y") + ") with angle " + @feature.get("featuredata").line_angle + " and length " @feature.get("featuredata").line_length + "."
    
  tableOk: => true
    
  tableHeader: () =>
    ["X Positon", "Y Position", "Angle", "Length"] 
    
  tableData: () =>
    [@feature.get("x"), @feature.get("y"), @feature.get("featuredata").line_angle, @feature.get("featuredata").line_length]
    
  render: (pjs) =>
    pjs.stroke 0, 180, 180
    pjs.strokeWeight 3
    pjs.noFill()
    pjs.line( @feature.get('featuredata').end_points[0][0],
              @feature.get('featuredata').end_points[0][1],
              @feature.get('featuredata').end_points[1][0],
              @feature.get('featuredata').end_points[1][1] )

plugin this, Line:LineFeature

