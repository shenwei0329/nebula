$(document).ready(function() {
	
	//统计图
	//Sparkline Charts
	$("#mini-chart-error").sparkline([1,4,6,2,0,5,6,4,6,3,7,4,2,8,5], {
    type: 'bar',
    height: '30px',
    barWidth: 6,
    barSpacing: 2,
    barColor: '#f35958',
    negBarColor: '#f35958'});
	//Sparkline Charts
	$("#mini-chart-run").sparkline([1,4,6,2,0,5,6,4,9,5,3,5,4,3], {
    type: 'bar',
    height: '30px',
    barWidth: 6,
    barSpacing: 2,
    barColor: '#0aa699',
    negBarColor: '#0aa699'});	
	//Sparkline Charts
	$("#mini-chart-stop").sparkline([1,4,6,2,0,5,6,4,5,9,2,4,7,2,6,8], {
    type: 'bar',
    height: '30px',
    barWidth: 6,
    barSpacing: 2,
    barColor: '#1f3853',
    negBarColor: '#1f3853'});	

//监控图变大变小
	$(' .fullscreen-on').click(function () { 
		$('#basic-info').hide();
		/*$('#basic-info').css('display','none');*/
		$(this).parent().parent().parent().parent().parent().css('width','100%');
		$(this).parent().css('display','none');
		$('.fullscreen-off').parent().css('display','inline-block');
	});
	$(' .fullscreen-off').click(function () {
		$('#basic-info').show(); 
		$(this).parent().parent().parent().parent().parent().css('width','66.6666666%');
		$(this).parent().css('display','none');
		$('.fullscreen-on').parent().css('display','inline-block');
	});

//虚拟机内的安全组删除
	$('.info-delete').click(function(){
	//	$(this).parent().css('display','none');
		 });
//操作日志内的具体时间显示	
	$('.detail-time').tooltip('toggle');
	$('.detail-time').tooltip('hide');


});
		
		