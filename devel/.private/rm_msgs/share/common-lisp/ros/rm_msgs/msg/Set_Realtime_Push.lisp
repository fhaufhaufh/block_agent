; Auto-generated. Do not edit!


(cl:in-package rm_msgs-msg)


;//! \htmlinclude Set_Realtime_Push.msg.html

(cl:defclass <Set_Realtime_Push> (roslisp-msg-protocol:ros-message)
  ((cycle
    :reader cycle
    :initarg :cycle
    :type cl:fixnum
    :initform 0)
   (port
    :reader port
    :initarg :port
    :type cl:fixnum
    :initform 0)
   (force_coordinate
    :reader force_coordinate
    :initarg :force_coordinate
    :type cl:fixnum
    :initform 0)
   (ip
    :reader ip
    :initarg :ip
    :type cl:string
    :initform ""))
)

(cl:defclass Set_Realtime_Push (<Set_Realtime_Push>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <Set_Realtime_Push>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'Set_Realtime_Push)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name rm_msgs-msg:<Set_Realtime_Push> is deprecated: use rm_msgs-msg:Set_Realtime_Push instead.")))

(cl:ensure-generic-function 'cycle-val :lambda-list '(m))
(cl:defmethod cycle-val ((m <Set_Realtime_Push>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader rm_msgs-msg:cycle-val is deprecated.  Use rm_msgs-msg:cycle instead.")
  (cycle m))

(cl:ensure-generic-function 'port-val :lambda-list '(m))
(cl:defmethod port-val ((m <Set_Realtime_Push>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader rm_msgs-msg:port-val is deprecated.  Use rm_msgs-msg:port instead.")
  (port m))

(cl:ensure-generic-function 'force_coordinate-val :lambda-list '(m))
(cl:defmethod force_coordinate-val ((m <Set_Realtime_Push>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader rm_msgs-msg:force_coordinate-val is deprecated.  Use rm_msgs-msg:force_coordinate instead.")
  (force_coordinate m))

(cl:ensure-generic-function 'ip-val :lambda-list '(m))
(cl:defmethod ip-val ((m <Set_Realtime_Push>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader rm_msgs-msg:ip-val is deprecated.  Use rm_msgs-msg:ip instead.")
  (ip m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <Set_Realtime_Push>) ostream)
  "Serializes a message object of type '<Set_Realtime_Push>"
  (cl:write-byte (cl:ldb (cl:byte 8 0) (cl:slot-value msg 'cycle)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 8) (cl:slot-value msg 'cycle)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 0) (cl:slot-value msg 'port)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 8) (cl:slot-value msg 'port)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 0) (cl:slot-value msg 'force_coordinate)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 8) (cl:slot-value msg 'force_coordinate)) ostream)
  (cl:let ((__ros_str_len (cl:length (cl:slot-value msg 'ip))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_str_len) ostream))
  (cl:map cl:nil #'(cl:lambda (c) (cl:write-byte (cl:char-code c) ostream)) (cl:slot-value msg 'ip))
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <Set_Realtime_Push>) istream)
  "Deserializes a message object of type '<Set_Realtime_Push>"
    (cl:setf (cl:ldb (cl:byte 8 0) (cl:slot-value msg 'cycle)) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 8) (cl:slot-value msg 'cycle)) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 0) (cl:slot-value msg 'port)) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 8) (cl:slot-value msg 'port)) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 0) (cl:slot-value msg 'force_coordinate)) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 8) (cl:slot-value msg 'force_coordinate)) (cl:read-byte istream))
    (cl:let ((__ros_str_len 0))
      (cl:setf (cl:ldb (cl:byte 8 0) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'ip) (cl:make-string __ros_str_len))
      (cl:dotimes (__ros_str_idx __ros_str_len msg)
        (cl:setf (cl:char (cl:slot-value msg 'ip) __ros_str_idx) (cl:code-char (cl:read-byte istream)))))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<Set_Realtime_Push>)))
  "Returns string type for a message object of type '<Set_Realtime_Push>"
  "rm_msgs/Set_Realtime_Push")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'Set_Realtime_Push)))
  "Returns string type for a message object of type 'Set_Realtime_Push"
  "rm_msgs/Set_Realtime_Push")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<Set_Realtime_Push>)))
  "Returns md5sum for a message object of type '<Set_Realtime_Push>"
  "9a0e0df44121dc8d27005a2fbd40ac91")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'Set_Realtime_Push)))
  "Returns md5sum for a message object of type 'Set_Realtime_Push"
  "9a0e0df44121dc8d27005a2fbd40ac91")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<Set_Realtime_Push>)))
  "Returns full string definition for message of type '<Set_Realtime_Push>"
  (cl:format cl:nil "uint16 cycle~%uint16 port~%uint16 force_coordinate~%string ip~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'Set_Realtime_Push)))
  "Returns full string definition for message of type 'Set_Realtime_Push"
  (cl:format cl:nil "uint16 cycle~%uint16 port~%uint16 force_coordinate~%string ip~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <Set_Realtime_Push>))
  (cl:+ 0
     2
     2
     2
     4 (cl:length (cl:slot-value msg 'ip))
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <Set_Realtime_Push>))
  "Converts a ROS message object to a list"
  (cl:list 'Set_Realtime_Push
    (cl:cons ':cycle (cycle msg))
    (cl:cons ':port (port msg))
    (cl:cons ':force_coordinate (force_coordinate msg))
    (cl:cons ':ip (ip msg))
))
