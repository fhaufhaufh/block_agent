; Auto-generated. Do not edit!


(cl:in-package rm_msgs-msg)


;//! \htmlinclude write_single_register.msg.html

(cl:defclass <write_single_register> (roslisp-msg-protocol:ros-message)
  ((port
    :reader port
    :initarg :port
    :type cl:fixnum
    :initform 0)
   (address
    :reader address
    :initarg :address
    :type cl:integer
    :initform 0)
   (data
    :reader data
    :initarg :data
    :type cl:fixnum
    :initform 0)
   (device
    :reader device
    :initarg :device
    :type cl:fixnum
    :initform 0))
)

(cl:defclass write_single_register (<write_single_register>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <write_single_register>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'write_single_register)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name rm_msgs-msg:<write_single_register> is deprecated: use rm_msgs-msg:write_single_register instead.")))

(cl:ensure-generic-function 'port-val :lambda-list '(m))
(cl:defmethod port-val ((m <write_single_register>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader rm_msgs-msg:port-val is deprecated.  Use rm_msgs-msg:port instead.")
  (port m))

(cl:ensure-generic-function 'address-val :lambda-list '(m))
(cl:defmethod address-val ((m <write_single_register>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader rm_msgs-msg:address-val is deprecated.  Use rm_msgs-msg:address instead.")
  (address m))

(cl:ensure-generic-function 'data-val :lambda-list '(m))
(cl:defmethod data-val ((m <write_single_register>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader rm_msgs-msg:data-val is deprecated.  Use rm_msgs-msg:data instead.")
  (data m))

(cl:ensure-generic-function 'device-val :lambda-list '(m))
(cl:defmethod device-val ((m <write_single_register>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader rm_msgs-msg:device-val is deprecated.  Use rm_msgs-msg:device instead.")
  (device m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <write_single_register>) ostream)
  "Serializes a message object of type '<write_single_register>"
  (cl:let* ((signed (cl:slot-value msg 'port)) (unsigned (cl:if (cl:< signed 0) (cl:+ signed 256) signed)))
    (cl:write-byte (cl:ldb (cl:byte 8 0) unsigned) ostream)
    )
  (cl:let* ((signed (cl:slot-value msg 'address)) (unsigned (cl:if (cl:< signed 0) (cl:+ signed 4294967296) signed)))
    (cl:write-byte (cl:ldb (cl:byte 8 0) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) unsigned) ostream)
    )
  (cl:let* ((signed (cl:slot-value msg 'data)) (unsigned (cl:if (cl:< signed 0) (cl:+ signed 65536) signed)))
    (cl:write-byte (cl:ldb (cl:byte 8 0) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) unsigned) ostream)
    )
  (cl:let* ((signed (cl:slot-value msg 'device)) (unsigned (cl:if (cl:< signed 0) (cl:+ signed 65536) signed)))
    (cl:write-byte (cl:ldb (cl:byte 8 0) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) unsigned) ostream)
    )
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <write_single_register>) istream)
  "Deserializes a message object of type '<write_single_register>"
    (cl:let ((unsigned 0))
      (cl:setf (cl:ldb (cl:byte 8 0) unsigned) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'port) (cl:if (cl:< unsigned 128) unsigned (cl:- unsigned 256))))
    (cl:let ((unsigned 0))
      (cl:setf (cl:ldb (cl:byte 8 0) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) unsigned) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'address) (cl:if (cl:< unsigned 2147483648) unsigned (cl:- unsigned 4294967296))))
    (cl:let ((unsigned 0))
      (cl:setf (cl:ldb (cl:byte 8 0) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) unsigned) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'data) (cl:if (cl:< unsigned 32768) unsigned (cl:- unsigned 65536))))
    (cl:let ((unsigned 0))
      (cl:setf (cl:ldb (cl:byte 8 0) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) unsigned) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'device) (cl:if (cl:< unsigned 32768) unsigned (cl:- unsigned 65536))))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<write_single_register>)))
  "Returns string type for a message object of type '<write_single_register>"
  "rm_msgs/write_single_register")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'write_single_register)))
  "Returns string type for a message object of type 'write_single_register"
  "rm_msgs/write_single_register")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<write_single_register>)))
  "Returns md5sum for a message object of type '<write_single_register>"
  "967b76240e09e64a48f1fbaa080ed555")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'write_single_register)))
  "Returns md5sum for a message object of type 'write_single_register"
  "967b76240e09e64a48f1fbaa080ed555")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<write_single_register>)))
  "Returns full string definition for message of type '<write_single_register>"
  (cl:format cl:nil "int8 port~%int32 address~%int16 data~%int16 device~%~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'write_single_register)))
  "Returns full string definition for message of type 'write_single_register"
  (cl:format cl:nil "int8 port~%int32 address~%int16 data~%int16 device~%~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <write_single_register>))
  (cl:+ 0
     1
     4
     2
     2
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <write_single_register>))
  "Converts a ROS message object to a list"
  (cl:list 'write_single_register
    (cl:cons ':port (port msg))
    (cl:cons ':address (address msg))
    (cl:cons ':data (data msg))
    (cl:cons ':device (device msg))
))
