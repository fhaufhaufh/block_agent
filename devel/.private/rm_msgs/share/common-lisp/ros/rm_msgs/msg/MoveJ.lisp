; Auto-generated. Do not edit!


(cl:in-package rm_msgs-msg)


;//! \htmlinclude MoveJ.msg.html

(cl:defclass <MoveJ> (roslisp-msg-protocol:ros-message)
  ((joint
    :reader joint
    :initarg :joint
    :type (cl:vector cl:float)
   :initform (cl:make-array 0 :element-type 'cl:float :initial-element 0.0))
   (speed
    :reader speed
    :initarg :speed
    :type cl:float
    :initform 0.0)
   (trajectory_connect
    :reader trajectory_connect
    :initarg :trajectory_connect
    :type cl:fixnum
    :initform 0))
)

(cl:defclass MoveJ (<MoveJ>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <MoveJ>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'MoveJ)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name rm_msgs-msg:<MoveJ> is deprecated: use rm_msgs-msg:MoveJ instead.")))

(cl:ensure-generic-function 'joint-val :lambda-list '(m))
(cl:defmethod joint-val ((m <MoveJ>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader rm_msgs-msg:joint-val is deprecated.  Use rm_msgs-msg:joint instead.")
  (joint m))

(cl:ensure-generic-function 'speed-val :lambda-list '(m))
(cl:defmethod speed-val ((m <MoveJ>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader rm_msgs-msg:speed-val is deprecated.  Use rm_msgs-msg:speed instead.")
  (speed m))

(cl:ensure-generic-function 'trajectory_connect-val :lambda-list '(m))
(cl:defmethod trajectory_connect-val ((m <MoveJ>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader rm_msgs-msg:trajectory_connect-val is deprecated.  Use rm_msgs-msg:trajectory_connect instead.")
  (trajectory_connect m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <MoveJ>) ostream)
  "Serializes a message object of type '<MoveJ>"
  (cl:let ((__ros_arr_len (cl:length (cl:slot-value msg 'joint))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_arr_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_arr_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_arr_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_arr_len) ostream))
  (cl:map cl:nil #'(cl:lambda (ele) (cl:let ((bits (roslisp-utils:encode-single-float-bits ele)))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream)))
   (cl:slot-value msg 'joint))
  (cl:let ((bits (roslisp-utils:encode-single-float-bits (cl:slot-value msg 'speed))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream))
  (cl:write-byte (cl:ldb (cl:byte 8 0) (cl:slot-value msg 'trajectory_connect)) ostream)
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <MoveJ>) istream)
  "Deserializes a message object of type '<MoveJ>"
  (cl:let ((__ros_arr_len 0))
    (cl:setf (cl:ldb (cl:byte 8 0) __ros_arr_len) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 8) __ros_arr_len) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 16) __ros_arr_len) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 24) __ros_arr_len) (cl:read-byte istream))
  (cl:setf (cl:slot-value msg 'joint) (cl:make-array __ros_arr_len))
  (cl:let ((vals (cl:slot-value msg 'joint)))
    (cl:dotimes (i __ros_arr_len)
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:aref vals i) (roslisp-utils:decode-single-float-bits bits))))))
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'speed) (roslisp-utils:decode-single-float-bits bits)))
    (cl:setf (cl:ldb (cl:byte 8 0) (cl:slot-value msg 'trajectory_connect)) (cl:read-byte istream))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<MoveJ>)))
  "Returns string type for a message object of type '<MoveJ>"
  "rm_msgs/MoveJ")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'MoveJ)))
  "Returns string type for a message object of type 'MoveJ"
  "rm_msgs/MoveJ")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<MoveJ>)))
  "Returns md5sum for a message object of type '<MoveJ>"
  "0c3946ceff2f0db7f69476a4971088db")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'MoveJ)))
  "Returns md5sum for a message object of type 'MoveJ"
  "0c3946ceff2f0db7f69476a4971088db")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<MoveJ>)))
  "Returns full string definition for message of type '<MoveJ>"
  (cl:format cl:nil "float32[] joint~%float32 speed~%uint8 trajectory_connect~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'MoveJ)))
  "Returns full string definition for message of type 'MoveJ"
  (cl:format cl:nil "float32[] joint~%float32 speed~%uint8 trajectory_connect~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <MoveJ>))
  (cl:+ 0
     4 (cl:reduce #'cl:+ (cl:slot-value msg 'joint) :key #'(cl:lambda (ele) (cl:declare (cl:ignorable ele)) (cl:+ 4)))
     4
     1
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <MoveJ>))
  "Converts a ROS message object to a list"
  (cl:list 'MoveJ
    (cl:cons ':joint (joint msg))
    (cl:cons ':speed (speed msg))
    (cl:cons ':trajectory_connect (trajectory_connect msg))
))
