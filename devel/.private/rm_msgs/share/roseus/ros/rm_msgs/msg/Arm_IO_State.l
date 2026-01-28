;; Auto-generated. Do not edit!


(when (boundp 'rm_msgs::Arm_IO_State)
  (if (not (find-package "RM_MSGS"))
    (make-package "RM_MSGS"))
  (shadow 'Arm_IO_State (find-package "RM_MSGS")))
(unless (find-package "RM_MSGS::ARM_IO_STATE")
  (make-package "RM_MSGS::ARM_IO_STATE"))

(in-package "ROS")
;;//! \htmlinclude Arm_IO_State.msg.html


(defclass rm_msgs::Arm_IO_State
  :super ros::object
  :slots (_Arm_Digital_Input ))

(defmethod rm_msgs::Arm_IO_State
  (:init
   (&key
    ((:Arm_Digital_Input __Arm_Digital_Input) (make-array 4 :initial-element 0 :element-type :integer))
    )
   (send-super :init)
   (setq _Arm_Digital_Input __Arm_Digital_Input)
   self)
  (:Arm_Digital_Input
   (&optional __Arm_Digital_Input)
   (if __Arm_Digital_Input (setq _Arm_Digital_Input __Arm_Digital_Input)) _Arm_Digital_Input)
  (:serialization-length
   ()
   (+
    ;; int8[4] _Arm_Digital_Input
    (* 1    4)
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; int8[4] _Arm_Digital_Input
     (dotimes (i 4)
       (write-byte (elt _Arm_Digital_Input i) s)
       )
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; int8[4] _Arm_Digital_Input
   (dotimes (i (length _Arm_Digital_Input))
     (setf (elt _Arm_Digital_Input i) (sys::peek buf ptr- :char)) (incf ptr- 1)
     (if (> (elt _Arm_Digital_Input i) 127) (setf (elt _Arm_Digital_Input i) (- (elt _Arm_Digital_Input i) 256)))
     )
   ;;
   self)
  )

(setf (get rm_msgs::Arm_IO_State :md5sum-) "5efdb4b2ffe84170bedb7e7c57e4e694")
(setf (get rm_msgs::Arm_IO_State :datatype-) "rm_msgs/Arm_IO_State")
(setf (get rm_msgs::Arm_IO_State :definition-)
      "int8[4] Arm_Digital_Input
#float32[4] Arm_Analog_Input

")



(provide :rm_msgs/Arm_IO_State "5efdb4b2ffe84170bedb7e7c57e4e694")


