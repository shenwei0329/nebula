 jQuery.validator.addMethod("normal_char", function(value, element) {    
      return this.optional(element) || /^[\u0391-\uFFE5\w]+$/.test(value);    
    }, "只能包括中文字、英文字母、数字和下划线"); 
 
 jQuery.validator.addMethod("digits", function(value, element) {    
	 return this.optional( element ) || /^-?\d+$/.test( value );  
 }, "只允许输入整数"); 

// 中文用户名验证   
jQuery.validator.addMethod("isValidChineseUsername", function(value, element) {
						var tel = /^[a-zA-Z\u0391-\uFFE5][a-zA-Z0-9\u0391-\uFFE5_-]{0,32}$/;
						return this.optional(element) || (tel.test(value));
					}, "可包含中文、字母、数字、下划线，首字符必须是中文、字母");
//必须大于
jQuery.validator.addMethod("biggerThan", function( value, element, param ) {
			// TODO find a way to bind the event just once, avoiding the unbind-rebind overhead
		//这方法应在使用前先有对数值类型的检查，否则结果不保证正确
			var target = $( param );
			if ( this.settings.onfocusout ) {
				target.unbind( ".validate-biggerThan" ).bind( "blur.validate-biggerThan", function() {
					$( element ).valid();
				});
			}
			return parseInt(value) > parseInt( target.val() );
		}, "大小不匹配");
//必须小于
jQuery.validator.addMethod("smallThan", function( value, element, param ) {
	//这方法应在使用前先有对数值类型的检查，否则结果不保证正确
	var target = $( param );
	if ( this.settings.onfocusout ) {
		target.unbind( ".validate-smallThan" ).bind( "blur.validate-smallThan", function() {
			$( element ).valid();
		});
	}
	return parseInt(value) <= parseInt( target.val() );
}, "大小不匹配");

// mac地址验证   
jQuery.validator.addMethod("isValidMacAddress", function(value, element) {
						var tel = /^[A-Fa-f0-9]{2}:[A-Fa-f0-9]{2}:[A-Fa-f0-9]{2}:[A-Fa-f0-9]{2}:[A-Fa-f0-9]{2}:[A-Fa-f0-9]{2}$/;
						return this.optional(element) || (tel.test(value));
					}, "请填写正确的mac地址，例如：00:50:56:21:a6:64");

// 电话号码验证   
jQuery.validator.addMethod("isValidPhone", function(value, element) {
						var tel = /^[0-9-#+]{6,20}$/;
						return this.optional(element) || (tel.test(value));
					}, "请填写正确的电话号码");

// 用户名验证   
jQuery.validator.addMethod("isValidUsername", function(value, element) {
						var tel = /^[a-zA-Z][a-zA-Z0-9_-]{0,32}$/;
						return this.optional(element) || (tel.test(value));
					}, "请填写正确的名称");
// IP验证，排除了1.1.1.255这种IP地址
jQuery.validator.addMethod("isValidIP", function(value, element) {
						var tel = /^(25[0-4]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9])\.(25[0-4]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-4]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-4]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[0-9])$/;
						return this.optional(element) || (tel.test(value));
					}, "请填写正确的IP地址");


jQuery.validator.addMethod("leastOneRequired", function(value, element , param ) {    
	var target = $( param );
	if ( this.settings.onfocusout ) {
		target.unbind( ".validate-leastOneRequired" ).bind( "blur.validate-leastOneRequired", function() {
			$( element ).valid();
		});
	}
	var checked = false ;
	$.each( target, function(i, box){
		if( $(box).attr("checked") ){
			checked = true ;
			return ;
		}
	});
	return checked ;
}, "只允许输入整数"); 
 
 jQuery.validator.addMethod("ip", function(value, element) {
	    var ip = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
	    return this.optional(element) || (ip.test(value) && (RegExp.$1 < 256 && RegExp.$2 < 256 && RegExp.$3 < 256 && RegExp.$4 < 256));
	}, "Ip地址格式错误");
 
 jQuery.validator.addMethod("ipRange", function(value, element) {
	 	if( this.optional(element) ) return true ;	//是可选项并且没有输入值的时候，直接返回
	 	
	 	var $select = $("select.subnet") ;
	 	var $option = $select.find("option:selected") ;
	 	
	 	if( !$option.attr("data-firstip") ||  !$option.attr("data-lastip")){
	 		return true ;
	 	}
	 	
	 	var firstip = $option.attr("data-firstip").split('.');
	 	var lastip = $option.attr("data-lastip").split('.');
	    
	    var firstOrInt = parseIpToInt( firstip ) ;
	    var lastOrInt = parseIpToInt(lastip) ;	    
	    
	    var inIp = value.split('.');
	    var inIpInt =parseIpToInt(inIp);
	 	var flag ;
	 	if( inIpInt >= firstOrInt && inIpInt <= lastOrInt ) {
	 		flag = true ;
	 	}else{
	 		flag = false ;
	 	};
	    return this.optional(element) || (flag);
	}, "请选择子网范围内的IP");

function parseIpToInt( ipArr ){
	 if ( !( ipArr instanceof Array) ){
		 console.log( "parseIpToInt : 传入参数非数组类型")
		 return -1 ;
	 }
	 if (ipArr.length != 4 ){
		 console.log( "parseIpToInt : 传入数组不是4个元素");
		 return -1 ;
	 }
	 return  parseInt(ipArr[0]) * 256 * 256 * 256 
		+ parseInt(ipArr[1]) * 256 * 256
		+ parseInt(ipArr[2]) * 256
		+ parseInt(ipArr[3]) ;
}
 
var baseName={
			rangelength:[4,16],
			required: true,
			normal_char:true
};
var baseDec={
		maxlength:50
};

var basePassword = {
	minlength : 4,
	maxlength : 16,
	required : true
};
var global_rule={
	newInstanceRule: {
		subnet_uuid:{
			required: true
		},
		ip_address: {
			isValidIP: true,
			ipRange:true
		},
		mac_address: {
			isValidMacAddress: true
		},
		bandwidth_tx: {
			digits: true
		},
		bandwidth_rx: {
			digits: true
		},
		display_name: baseName,
		volume_uuid:{
			required:true
		},
		display_description: baseDec

	},
	updateInstanceRule: {
		display_name: baseName,
		display_description: baseDec
	},
	/////////////// 网络，路由相关 start  //////////////////////////
	newRouterRule:{//新建路由
			name:baseName,
			description:baseDec
	},
	deleteRouterRule:{//删除路由
			name:baseName
	},
	updateRouterRule:{
		name:baseName,
		description:baseDec
	},
		newPrivateNetworkRule:{//新建私有网络
			name:baseName,
			description:baseDec,
			segmentation_id:{
				digits:true,
				range: [1,4094]
			}
			
		},
        updatePrivateNetworkRule:{//修改私有网络
        	name:baseName,
			description:baseDec

		},
        deletePrivateNetworkRule:{//修改私有网络
        	baseName:baseName
		},
        createSubnetRule:{
        	name:baseName,
			description:baseDec

		},
        createPortRule:{
        	name:baseName,
			description:baseDec

		},
		bandwidthSettingRule:{//带宽设置
			name:baseName,
			description:baseDec
			
		},
		bindPrivateNetworkRule:{//路由器绑定私有网络
			network_id:{
				required: true
			}
			
		},
		bindIpRule:{//绑定外部IP
			virtualrouter_publicip_id:{
				required: true
			}
		},
        unbindIpRule:{//解绑外部IP
			virtualrouter_publicip_id:{
				required: true
			}
		},
		newNetworkMappingRule:{//新建网络映射
			name:baseName,
			description:baseDec,
			virtualrouter_floatingip_id:{
				required:true
			},
            proto:{
                required:true
            },
			src_port:{
				digits:true,
				required: true,
				rangelength:[2,8]
			},
			dest_ip:{
				required: true,
				ip:true
			},
			dest_port:{
				digits:true,
				required: true,
				rangelength:[2,8]
			}
		},
		addSubnetRule:{
			name:baseName,
			description:baseDec,
			cidr:{
				required:true,
				ip:true
			},
			cidr_value:{
				required:true,
				digits:true,
				range:[0,32] 
			},
			gateway_ip:{
				required:true,
				ip:true
			},
			dns_nameservers:{
				required:true,
				ip:true
			},
			_start_ip:{
				ip:true
			},
			_end_ip:{
				ip:true
			},
			_ip_:{
				ip:true
			},
			_net_:{
				ip:true
			}
		},
		inVMRule:{
			subnet_id:{
				required:true
			},
			instance_id:{
				required:true
			}
			
		},
        outVMRule:{
        	port_id:{
				required:true
			}

		},
		connectRouterRule:{
			virtualrouter_id:{
				required:true
			}
			
		},
        tearRouterRule:{
        	name:baseName,
			description:baseDec

		},
		toVMRule:{
			name:baseName,
			description:baseDec
			
		},
		///////////// 网络，路由相关 end  //////////////////////////
		
		backupVMRule:{//备份虚拟机
			name:baseName
		},
		
		
		////////////////////////////////安全组start
		updateSecurityGroupRule:{//修改安全组
			name:baseName,
			description:baseDec
			
		},
		newSecurityGroupRule:{//新建安全组
			name:baseName,
			description:baseDec
			
		},
		toVMGroupRule:{//应用到虚拟机
			port_id:{
				required: true
			}
			
		},
        deleteGroupRule:{//应用到虚拟机
			baseName:baseName
		},
		newSecurityGroupRulesRule:{//新建安全组规则
			name:baseName,
			protocol: {
				required: true
			},
			direction: {
				required: true
			}
		},
		////////////////////////////////安全组end
		
		////////////////////////////////用户管理start
		newUserRule:{//新建用户
			username:{
				required: true,
				rangelength:[3,16],
				normal_char:true
			},
			password : basePassword ,
			cores:{
				maxlength: 10,
				required: true,
				digits: true,
				min: 1
			},
			ram:{
				maxlength: 10,
				required: true,
				digits: true,
				min: 1
			},
			email: {
				required: true,
				email: true
			},
			phone: {
				isValidPhone: true
			},
			volumes: {
				required: true,
				digits: true,
				min: 1
			},
			instances: {
				required: true,
				digits: true,
				min: 1
			},
			images: {
				required: true,
				digits: true,
				min: 1
			},
			virtual_routers: {
				required: true,
				digits: true,
				min: 1
			},
			private_networks: {
				required: true,
				digits: true,
				min: 1
			},
			bandwidth_tx: {
				required: true,
				digits: true,
				min: 1
			},
			bandwidth_rx: {
				required: true,
				digits: true,
				min: 1
			},
			firewalls: {
				required: true,
				digits: true,
				min: 1
			}
		},

        resetPwdRule:{
			password:basePassword,
			confirm_password: {
	            equalTo: "#password"
			}
		},
		////////////////////////////////用户管理end
		
		/////////////////////////////角色管理start
		newRoleRule:{
			name:{
				minlength: 5,
	            required: true
			},
			permissions:{
				required: true
			}
		},
		
		updateUserRule:{
			
		},
		
		updatePermissionsRule:{
			
		},
		
		
		/////////////////////////角色管理end
		
		/////////////////个人管理start
		changePwdRule:{
			password:basePassword,
			new_password:basePassword,
			confirm_password : {
	            equalTo: "#new_password"
			}
		},
		
		/////////////////个人管理end
		
		iopsRangeRule:{//修改虚拟机
			iops:{
				digits:true,
				required: true,
				range: [0,1000]
			}
		},
		memRangeRule:{//修改虚拟机
			vcpus:{
				required: true,
				digits:true
			},
			ram:{
				required: true,
				digits:true
			}
		},
		////////////////////////////////数据卷规则start
		newVolumeRule:{//新建数据卷
			name: baseName,
			size:{
				required : true,
				digits:true,
				min : 1 ,
				smallThan : "#vo_usable_quota"
			},
			description:baseDec,
			cinder_types:{
				required : true
			}
		},
		volumeToVMRule:{//挂载到虚拟机
			instance_id:{
				 required : true
			}
		},
		updateVolumeRule:{//修改数据卷
			name:baseName,
			description : baseDec
		},
        deleteVolumeRule:{//修改数据卷
			name:baseName
		},
		cloneVolumeRule:{//克隆数据卷
			name:baseName
		},
        extendVolumeRule:{//扩容数据卷

		},
		recoverVolumeRule:{//恢复数据卷
			volume_backup_id:{
				required: true
			}
		},
		backupVolumeRule:{//备份数据卷
			name:baseName
		},
		expansionVolumeRule:{//备份数据卷
			
		},
		updateVolumeBackRule:{
			name:baseName
		},
		////////////////////////////////数据卷规则end

	newAggregateRule:{
		name:{
			minlength: 2,
			maxlength: 30,
			required: true,
			normal_char: true
		},
		zone:{
			minlength: 2,
			maxlength: 30,
			required: true,
			normal_char: true
		}
	},

        ////////////////////////////////主机规则start
        newHostRule:{//新建主机
			hostname:{
				minlength: 2,
				maxlength: 32,
	            		required: true,
				isValidChineseUsername: true
			},
			host_ip:{
				required: true,
				isValidIP: true,
			},
			os_user: {
				maxlength: 32,
				isValidUsername: true,
				required: true
			}

		},
	updateHostRule:{
        hostname: {
			minlength: 2,
			maxlength: 32,
			required: true,
			isValidChineseUsername: true
		},
        os_user: {
            maxlength: 32,
            isValidUsername: true,
            required: true
        }
    },
        ////////////////////////////////主机规则end


        ////////////////////////////////镜像start
        UpdateInstanceBackup:{//修改虚拟机备份
				name:baseName
		},
       
       vmBackUpRule:{//修改虚拟机备份
				name:{
					minlength: 2,
		            required: true
				}
		},
        ////////////////////////////////镜像end
	attachPortRule: {
		upper_limit: {
			required:true,
			digits: true,
			min : 0,
			max : 1000000
		},
		floor_limit: {
			required:true,
			digits: true,
			min : 0,
			max : 1000000
		},
        ip : {
            isValidIP: true,
			ipRange:true
        },
        sgroup_id : {
        	//required : true 
        },
        mac_addr: {
			isValidMacAddress: true
		}
	},
	passwordIdenticalRule: {
		password:{
			minlength: 6,
			maxlength: 20,
			required: true
		},
		confirm_password:{
			minlength: 6,
			maxlength: 20,
			required: true,
			equalTo: "#password"
		}
	},
	newSecurityRule: {
		name: baseName,
		description: baseDec
	},
	settingsRule : {
		instance_attach_volumes:{
			required: true,
			maxlength: 2,
			digits : true
		},
		instance_attach_ports:{
			required: true,
			maxlength: 1,
			digits : true
		},
		instance_backups:{
			required: true,
			maxlength: 2,
			digits : true
		},
		instance_cores_min :{
			required: true,
			maxlength: 3,
			digits : true
		},
		instance_cores_max :{
			required: true,
			maxlength: 3,
			digits : true,
			biggerThan : "input[name='instance_cores_min']"
		},
		instance_ram_min :{
			required: true,
			maxlength: 6,
			digits : true
		},
		instance_ram_max :{
			required: true,
			maxlength: 6,
			digits : true,
			biggerThan : "input[name='instance_ram_min']"
		},
		volume_backups :{
			required: true,
			maxlength: 2,
			digits : true
		},
		volume_capacity :{
			required: true,
			maxlength: 6,
			digits : true
		},
		network_vlan_min :{
			required: true,
			maxlength: 4,
			digits : true
		},
		network_vlan_max :{
			required: true,
			maxlength: 4,
			digits : true,
			biggerThan : "#network_vlan_min"
		}
		
	},
	newPrivateImage : {
		name:baseName,
		os_type:{
			required : true 
		},
		disk_format : {
			required : true
		},
		container_format : {
			required : true 
		}
	},
    UpdateImageRule:{// 修改镜像
			name:baseName
	},
	securityGroupApply : {
		sgroup_id : {
			required : true
		}
	},
	createAlarmRule : {
		alarm_name : baseName,
		alarm_type : {
			required:true
		},
		alarm_period : {
			required : true
		},
		meter_rules : {
			required : true,
			minlength : 3 
		},
		alarm_action : {
			leastOneRequired : "#three :checkbox" 
		}
		
	},
	applyAlarmRule : {
		alarm_tmpl_id : {
			required : true
		}
	},
	t_aggregateRemoveHostRule : {
		host_id : {
			required : true,
		}
	},
	noRule: {}
};

var global_message={
		newInstanceRule : {
			subnet_uuid:{
				required : "必须指定子网"
			},
			volume_uuid:{
				required : "请选择一个大小合适的系统卷"
			},
			instance_batches:{
				max : "配额限制，最多可创建 {0}个虚拟机"
			}
		},
		toVMGroupRule:{
			port_id:{
				required: "请选择要接入的虚拟机"
			}
		},
		newPrivateImage : {
			name : {
				required : "请填写镜像名称"
			},
			os_type : {
				required : " 请选择操作系统类型 "
			},
			disk_format : {
				required : " 请选择镜像格式 "
			},
			container_format : {
				required : " 请选择容器格式"
			}
		},
		newRoleRule:{
			name : {
				required : "请填写角色名称"
			},
			permissions:{
				required: "请选择需要的权限"
			}
		},
		settingsRule : {
			instance_cores_max : {
				biggerThan : "最大值必须大于最小值"
			},
			instance_ram_max : {
				biggerThan : "最大值必须大于最小值"
			},
			network_vlan_max : {
				biggerThan : "最大值必须大于最小值"
			}
		},
		securityGroupApply : {
			sgroup_id : {
				required : "必须选择虚拟防火墙"
			}
		},
		newVolumeRule:{//新建数据卷
			size:{
				smallThan : "输入的容量超出您的可用配额"
			},
			description: "注意书写！"
		},
		createAlarmRule : {
			alarm_name : {
				required : "请填写名称"
			},
			alarm_type : {
				required:"请指定资源类型"
			},
			alarm_period : {
				required : "请指定告警周期"
			},
			meter_rules : {
				required : "必须设定一个或多个监控规则",
				minlength : "必须设定一个或多个监控规则" 
			},
			alarm_action : {
				leastOneRequired : "至少有一个触发条件" 
			}
		},
		applyAlarmRule : {
			alarm_tmpl_id : {
				required : "请指定一个告警策略"
			}
		},
        changePwdRule : {
            confirm_password : {
	            equalTo: "两次填写的密码不一致"
			}
        },
        resetPwdRule : {
            confirm_password : {
	            equalTo: "两次填写的密码不一致"
			}
        },
		t_aggregateRemoveHostRule : {
			host_id : {
				required : "至少选择一个主机",
				minlength : "至少选择一个主机",
				maxlength : "只能选择一个主机"
			}
		}
		
		
};
