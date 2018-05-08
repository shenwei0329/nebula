$(document).ready(function() {

	$('.usage').popover('toggle');
	$('.usage').popover('hide');

    $('.1-usage').easyPieChart({lineWidth:9,barColor:'#f35958',trackColor:'#e5e9ec',scaleColor:false});
    $('.2-usage').easyPieChart({lineWidth:9,barColor:'#f9ba46',trackColor:'#e5e9ec',scaleColor:false});
    $('.3-usage').easyPieChart({lineWidth:9,barColor:'#0090d9',trackColor:'#e5e9ec',scaleColor:false});
    $('.4-usage').easyPieChart({lineWidth:9,barColor:'#0aa699',trackColor:'#e5e9ec',scaleColor:false});
});