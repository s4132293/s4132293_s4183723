import pyhtml

import student_a_level_1
import student_a_level_2
import student_a_level_3
import student_b_level_1
import student_b_level_2
import student_b_level_3

pyhtml.need_debugging_help = True

#(A pages)
pyhtml.MyRequestHandler.pages["/"] = student_a_level_1
pyhtml.MyRequestHandler.pages["/level2a"] = student_a_level_2
pyhtml.MyRequestHandler.pages["/level3a"] = student_a_level_3

#(B pages)
pyhtml.MyRequestHandler.pages["/level1b"] = student_b_level_1
pyhtml.MyRequestHandler.pages["/level2b"] = student_b_level_2
pyhtml.MyRequestHandler.pages["/level3b"] = student_b_level_3

pyhtml.host_site()
