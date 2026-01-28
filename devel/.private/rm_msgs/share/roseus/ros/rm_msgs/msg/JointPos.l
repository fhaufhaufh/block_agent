;; Auto-generated. Do not edit!


(when (boundp 'rm_msgs::JointPos)
  (if (not (find-package "RM_MSGS"))
    (make-package "RM_MSGS"))
  (shadow 'JointPos (find-package "RM_MSGS")))
(unless (find-package "RM_MSGS::JOINTPOS")
  (make-package "RM_MSGS::JOINTPOS"))

(in-package "ROS")
;;//! \htmlinclude JointPos.msg.html


(defclass rm_msgs::JointPos
  :super ros::object
  :slots (_joint _expand ))

(defmethod rm_msgs::JointPos
  (:init
   (&key
    ((:joint __joint) (make-array 0 :initial-element 0.0 :element-type :float))
    ((:expand __expand) 0.0)
    )
   (send-super :init)
   (setq _joint __joint)
   (setq _expand (float __expand))
   self)
  (:joint
   (&optional __joint)
   (if __joint (setq _joint __joint)) _joint)
  (:expand
   (&optional __expand)
   (if __expand (setq _expand __expand)) _expand)
  (:serialization-length
   ()
   (+
    ;; float32[] _joint
    (* 4    (length _joint)) 4
    ;; float32 _expand
    4
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; float32[] _joint
     (write-long (length _joint) s)
     (dotimes (i (length _joint))
       (sys::poke (elt _joint i) (send s :buffer) (send s :count) :float) (incf (stream-count s) 4)
       )
     ;; float32 _expand
       (sys::poke _expand (send s :buffer) (send s :count) :float) (incf (stream-count s) 4)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; float32[] _joint
   (let (n)
     (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4)
     (setq _joint (instantiate float-vector n))
     (dotimes (i n)
     (setf (elt _joint i) (sys::peek buf ptr- :float)) (incf ptr- 4)
     ))
   ;; float32 _expand
     (setq _expand (sys::peek buf ptr- :float)) (incf ptr- 4)
   ;;
   self)
  )

(setf (get rm_msgs::JointPos :md5sum-) "278dfe354f7a05e095637c9789d0fcfe")
(setf (get rm_msgs::JointPos :datatype-) "rm_msgs/JointPos")
(setf (get rm_msgs::JointPos :definition-)
      "#control arm joints without planning

float32[] joint
float32    expand
")



(provide :rm_msgs/JointPos "278dfe354f7a05e095637c9789d0fcfe")


