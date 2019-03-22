import numpy as np
import pandas as pd
import scipy.optimize as opt
import sugawara
from sugawara import simulate, calibrate
from bokeh.io import curdoc
from bokeh.layouts import widgetbox,gridplot, column, row
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import Slider, TextInput,  Panel, Tabs, Div, Button,RadioGroup
from bokeh.plotting import figure, show
from bokeh.models.tools import HoverTool, WheelZoomTool
from bokeh.models import Title,LinearAxis, Range1d
from bokeh.models.widgets import DataTable, DateFormatter, TableColumn

    
def loadParam():
    s_row = 0                                                                                   # Function to import pre-saved Parameters
    afp='para.txt'
    fp = pd.read_csv(afp, skiprows=s_row, skipinitialspace=True, index_col = False)
    w_k1.value = str(fp['k1'][0])
    w_k2.value = str(fp['k2'][0])
    w_k3.value = str(fp['k3'][0])
    w_k4.value = str(fp['k4'][0])
    w_d1.value = str(fp['d1'][0])
    w_d2.value = str(fp['d2'][0])
    w_rfcf.value = str(fp['rfcf'][0])
    w_ecorr.value = str(fp['ecorr'][0])

def runModel():                                                                                     # Function to run Sugawara Model
    s_row = 0                                                                                       # Function to import pre-saved Parameters
    afp='para.txt'
    fp = pd.read_csv(afp, skiprows=s_row, skipinitialspace=True, index_col=False)
    _k1 = fp['k1'][0]
    _k2 = fp['k2'][0]
    _k3 = fp['k3'][0]
    _k4 = fp['k4'][0]
    _d1 = fp['d1'][0]
    _d2 = fp['d2'][0]
    _rfcf = fp['rfcf'][0]
    _ecorr = fp['ecorr'][0]
   
    extra_pars = [1, 147.0]       
    pars = [_k1,_k2,_k3,_k4,_d1,_d2,_rfcf,_ecorr]                                                        # Parameters to be used during simulation

    new_f= str(w_fn.value)
    skip_rows = 16  
    data = pd.read_csv(new_f,                                      
                       skiprows=skip_rows,
                       skipinitialspace=True)
    time_index = pd.date_range('1994 12 07 20:00', periods=len(data), freq='H')
    data.insert(loc=0, column='DateTime', value = time_index)                   # To use precipitation data and ET data
    prec = np.array(data['Rainfall']) + np.array(data['Snowfall'])              # loaded earlier for simulation
    evap = np.array(data['ActualET'])
    q_sim, st_sim = sugawara.simulate(prec=prec[:-1],                           # Run Sugawara Model
                                  evap=evap[:-1], 
                                  param=pars, 
                                  extra_param=extra_pars)  # Run the model
    Format_q_sim = [ '%.3f' % elem for elem in q_sim]                           # Rounding off simulated discharge into 3 decimal pt
    S1 = [None]*len(q_sim)
    S2 = [None]*len(q_sim)         
    
    for t in range(len(q_sim)):
        S1[t] = float(st_sim[t][0])                                             # Store States into two lists respectively
        S2[t] = float(st_sim[t][1])
    
    # Update Glyphs
    ds3.data = {'x':data['DateTime'],'y':q_sim}                                # Update glyphs with newly simulated data
    ds4.data = {'x':data['DateTime'],'y':S1}
    ds5.data = {'x':data['DateTime'], 'y':S2}
    
    # Update Data Table
    time = data['Time'].tolist()                                         # Convert all from Pandas DF into lists, for consistency
    Qrec = data['Qrec'].tolist()
    Rain = data['Rainfall'].tolist()
    ET = data['ActualET'].tolist()
    source2.data = {'x':time, 'y':Qrec, 'y1':Format_q_sim, 'y2':Rain, 'y3':ET}         # Update Data Table
     
    # Update Error Table for NSE and RMSE
    NSE_total = sugawara.NSE(q_sim,data['Qrec'], q='def', j=2.0)                  # Calcalate and update Error Data Table
    NSE = round(NSE_total,3)
    
    RMSE_list = []
    for j in range(len(q_sim)):
        val = round((q_sim[j] - data.iloc[j,3])**2.0,3)
        RMSE_list.append(val)
    RMSE = round((sum(RMSE_list)/len(q_sim))**0.5,3)    
    source.data = dict(ErrorIndicator =['NSE', 'RMSE'], measurement=[str(NSE), str(RMSE)])


def loadInputFile(): 
    new_f = str(w_fn.value)                                              # Load Input File using Text Input File Name
    skip_rows = 16  

    data = pd.read_csv(new_f,                                            # Use Pandas DF to read file                                 
                       skiprows=skip_rows,
                       skipinitialspace=True)
    
    time_index = pd.date_range('1994 12 07 20:00', periods=len(data), freq='H') # Create time indices
    
    data.insert(loc=0, column='DateTime', value = time_index)   
    
    # Update Glyphs
    ds.data = {'x':data['DateTime'], 'y':data['Rainfall']}                       # Update glpyhs
    ds1.data = {'x':data['DateTime'], 'y':data['ActualET']}
    ds2.data = {'x':data['DateTime'], 'y':data['Qrec']}
    
    # Update Data Table               
    time = data['Time'].tolist()                                         # Update Data Table 
    Qrec = data['Qrec'].tolist()                                         # First convert all into lists for consistency
    Rain = data['Rainfall'].tolist()
    ET = data['ActualET'].tolist()
    source2.data = {'x':time, 'y':Qrec,'y1':q_sim, 'y2':Rain, 'y3':ET}               # Update Data Table
    

def calibrateModel():
    new_f = str(w_fn.value)                                              # Calibrate Model
    skip_rows = 16  
    data = pd.read_csv(new_f,
                       skiprows=skip_rows,
                       skipinitialspace=True)
    time_index = pd.date_range('1994 12 07 20:00', periods=len(data), freq='H')
    data.insert(loc=0, column='DateTime', value = time_index)  
    prec = np.array(data['Rainfall']) + np.array(data['Snowfall'])
    evap = np.array(data['ActualET'])
    extra_pars = [1, 147.0]
    pars, NSE = calibrate(prec, evap, extra_pars, data['Qrec'], verbose=False)  # Calibrate Model by passing into function
    
    q_sim, st_sim = simulate(prec=prec[:-1],                           # based on calibrated parameters, re-run results
                                  evap=evap[:-1], 
                                  param=pars, 
                                  extra_param=extra_pars)
    Format_q_sim = [ '%.3f' % elem for elem in q_sim]                           # Obtain calibrated q_sim and states
    S1 = [None]*len(q_sim)                                                      # Convert into 3 decimal places
    S2 = [None]*len(q_sim)
    
    for t in range(len(q_sim)):                  
        S1[t] = float(st_sim[t][0])
        S2[t] = float(st_sim[t][1])
    
    # Update Glyphs                                                             # Update Glyphs
    ds3.data = {'x':data['DateTime'], 'y':q_sim}
    ds4.data = {'x':data['DateTime'], 'y':S1}
    ds5.data = {'x':data['DateTime'], 'y':S2}
    
    # Update Data Table                                                         # Update Data Table
    time = data['Time'].tolist()
    Qrec = data['Qrec'].tolist()
    Rain = data['Rainfall'].tolist()
    ET = data['ActualET'].tolist()
    source2.data = {'x ':time,'y':Qrec, 'y1':Format_q_sim, 'y2':Rain, 'y3':ET}
    
    # Update Parameters Table
    index_para = ['k1','k2','k3','k4','d1','d2','rfcf','ecorr']                 
    Formattedpars = [ '%.3f' % elem for elem in pars]                          # Update Parameter Table
    source3.data = {'x':index_para, 'y':Formattedpars}
    
    for elem in Formattedpars:
        para_formatted.append(elem)                                            # Update parameter list outside function 
    
    # Update Error Table
    NSE_total = sugawara.NSE(q_sim,data['Qrec'], q='def',j=2.0)                 # Update Error Table
    NSE = round(NSE_total,3)
    RMSE_list = []
    for j in range(len(q_sim)):
        val = round((q_sim[j] - data.iloc[j,3])**2.0,3)
        RMSE_list.append(val)
    RMSE = round((sum(RMSE_list)/len(q_sim))**0.5,3)
    source.data = dict(ErrorIndicator =['NSE', 'RMSE'], measurement=[str(NSE), str(RMSE)])
 
    
#                               Load Empty ASC File                          #
skip_rows = 16  # Number of rows to skip in the output file
output_file = 'empty.asc'                                                       # Pass an empty file to reflect empty glpyhs
    
# Read data from the output file
data = pd.read_csv(output_file,                                                 # Read empty file 
                   skiprows=skip_rows,
                   skipinitialspace=True)
time_index = pd.date_range('1994 12 07 20:00', periods=len(data), freq='H')
data.insert(loc=0, column='DateTime', value = time_index)  

#                                     Empty Lists                   ##

q_sim = [0.0]*len(data['DateTime'])                                             # Create empty lists so glyphs are emtpy                            
S1 = [0.0]*len(data['DateTime'])
S2 = [0.0]*len(data['DateTime'])
NSE = "N.A."                                                                    # Errors are empty at the beginning
RMSE =  "N.A."   
ds = ColumnDataSource({'x':data['DateTime'], 'y':data['Rainfall']})              # Map data to ColumnDataSource for plotting
ds1 = ColumnDataSource({'x':data['DateTime'], 'y':data['ActualET']}) 
ds2 = ColumnDataSource({'x':data['DateTime'],'y':data['Qrec']}) 
ds3= ColumnDataSource({'x':data['DateTime'], 'y':q_sim}) 
ds4= ColumnDataSource({'x':data['DateTime'],'y':S1})   
ds5= ColumnDataSource({'x':data['DateTime'], 'y':S2})   

                            
#  Plotting and Assigning to Glyph / Hover Tools   

# Figures setup
prain = figure(width=800,                                                       # Set up Figures, with widths, heights and features
               height=280, 
               x_axis_type="datetime", 
               title='Rainfall and Evapotranspiration Data',
               tools='pan, wheel_zoom, zoom_in, zoom_out, box_select, lasso_select, tap')
pdischarge = figure(width=800,
                    height=280,
                    x_axis_type="datetime", 
                    title='Observed Flow and Simulated Flow',
                    tools='pan, wheel_zoom, zoom_in, zoom_out, box_select, lasso_select, tap') 
pstorage= figure(width=800,
                    height=280,
                    x_axis_type="datetime", 
                    title='States (mm)',
                    tools='pan, wheel_zoom, zoom_in, zoom_out, box_select, lasso_select, tap') 

prain.extra_y_ranges = {"ET": Range1d(start=0.4,end=0)}                         # Set up an inverted axis for ET

# Adding a line plot to the figures
prain.line(x='x', y='y', line_width=1, color='gray',legend="Rainfall", source=ds)   # Add line to plot Rainfall and ET
prain.line(x='x', y='y', line_width=1, color='red',legend="ET",source=ds1,y_range_name="ET")

pdischarge.line(x='x', y='y', line_width=1, color='blue',legend ='Qrec',source=ds2) # Add line to plot discharges
pdischarge.line(x='x', y='y' ,line_width=1, color='green',legend ='Qsim',source=ds3) 
pstorage.line(x='x', y='y',line_width=1, color='red',legend ='State1  (S1)',source=ds4) # Add line to plot states
pstorage.line(x='x', y='y',line_width=1, color='blue',legend ='State2 (S2)',source=ds5) 

prain.yaxis.axis_label = "Rainfall"
prain.add_layout(Title(text="Date and Time", align="center"), "below") 
prain.add_layout(LinearAxis(y_range_name="ET", axis_label ="Evapotranspiration"), 'right') # Indicate secondary axis location
  
pdischarge.add_layout(Title(text="Date and Time", align="center"), "below")    # labbeling Title and axis labels
pstorage.add_layout(Title(text="Date and Time", align="center"), "below")  
prain.legend.orientation = "horizontal"
pdischarge.legend.orientation = "horizontal"
pstorage.legend.orientation = "horizontal"
pdischarge.yaxis.axis_label = "Discharge"
pstorage.yaxis.axis_label = "States"

# Creating a circle plot in top of the line (as markers)
cr = prain.circle(x='x', y='y', size=5.0,                                       # Hover markers
fill_color="grey", hover_fill_color="firebrick",
fill_alpha=0.05, hover_alpha=0.3,
line_color=None, hover_line_color="white",source=ds)

cr1 = pdischarge.circle(x='x', y='y', size=5.0,
fill_color="grey", hover_fill_color="navy",
fill_alpha=0.05, hover_alpha=0.3,
line_color=None, hover_line_color="white",source=ds2)

cr2 = pstorage.circle(x='x', y='y', size=5.0,
fill_color="grey", hover_fill_color="orange",
fill_alpha=0.05, hover_alpha=0.3,
line_color=None, hover_line_color="white",source=ds4)

cr3 = pdischarge.circle(x='x', y='y', size=5.0,
fill_color="grey", hover_fill_color="navy",
fill_alpha=0.05, hover_alpha=0.3,
line_color=None, hover_line_color="white",source=ds3)
   
cr4 = pstorage.circle(x='x', y='y', size=5.0,
fill_color="grey", hover_fill_color="orange",
fill_alpha=0.05, hover_alpha=0.3,
line_color=None, hover_line_color="white",source=ds5)

# Configuring the Hover tool to display data
hover_tool = HoverTool(tooltips=None,                                           # set tooltips
                       line_policy='none', 
                       renderers=[cr],                                          # which plot will appear
                       mode='mouse')                                            # mouse
hover_tool.tooltips = [("index", "$index"),
                       ("Rainfall", "$y")]

hover_tool1 = HoverTool(tooltips=None,  
                       line_policy='none', 
                       renderers=[cr1],                     
                       mode='mouse')  
hover_tool1.tooltips = [("index", "$index"),
                       ("Qrec", "$y")]

hover_tool2 = HoverTool(tooltips=None,  
                       line_policy='none', 
                       renderers=[cr2],
                       mode='mouse')  
hover_tool2.tooltips = [("index", "$index"),
                       ("S1", "$y)"),]

hover_tool3 = HoverTool(tooltips=None,  
                       line_policy='none', 
                       renderers=[cr3], 
                       mode='mouse')  
hover_tool3.tooltips = [("index", "$index"),
                       ("Qsim", "$y)"),]

hover_tool4 = HoverTool(tooltips=None,  
                       line_policy='none',
                       renderers=[cr4], 
                       mode='mouse') 
hover_tool4.tooltips = [("index", "$index"), ("S2", "$y)"),]

# Here we add the tools.                                                          # Map however tools to plots
mouse_zoom = WheelZoomTool()
prain.add_tools(hover_tool)
pdischarge.add_tools(hover_tool1)
pdischarge.add_tools(hover_tool3)
pstorage.add_tools(hover_tool2)
pstorage.add_tools(hover_tool4)

#                             Widgets                                                          # Insert Title of the Page
heading = Div(text="<h1 align = 'center' style='color:#0000FF'><h2><b> SUGAWARA MODEL </h1>"
              ,width = 300, height = 5)

# To Load Input File
w_fn = TextInput(placeholder="---.asc",                                             # Create Text Input box for Filename
                title="Enter filename e.g. output.asc")
w_loadinput = Button(label='Load Data', button_type="success")
w_loadinput.on_click(loadInputFile)


# To Load Parameter File
w_k1 = TextInput(placeholder="hint: 0.0 - 1.1",                              # Create Text Input Box for keying-in parameters
                title="k1 - Upper Outlet Discharge")
w_k2 = TextInput(placeholder="hint: 0.0 - 1.1",
                 title="k2 -  Lower Outlet Discharge")
w_k3 = TextInput(placeholder="hint: 0.0 - 1.5",
                  title="k3 -  Bottom Outlet Discharge")
w_k4 = TextInput(placeholder=" hint: 0.0 - 1.1",
                  title="k4 -  Bottom Tank Discharge Coefficient")
w_d1 = TextInput(placeholder="hint: 1 - 15",
                 title="d1 - Upper Outlet Position")
w_d2 = TextInput(placeholder="hint: 0.1 - 1.0",
                  title="d2 - Lower Outlet Position")
w_rfcf = TextInput(placeholder="hint: 0.8 - 1.2",
                  title="rfcf - Rainfall Error Correction Factor")
w_ecorr = TextInput(placeholder="Hint: 0.8 - 1.2",
                  title="ecorr - Discharge Error Correction Factor")
w_loadpara = Button(label='Load Parameter File', button_type="success")         # Create button for loading and saving parameters
#w_savepara = Button(label='Save Parameters', button_type="success")
#w_savepara.on_click(saveParam)                                                  # Button to run save parameters function
w_loadpara.on_click(loadParam)                                                  # Button to load parameters function


# DataTable 1 for Q
datatable1 = {'x':data['Time'],'y':data['Qrec'], 'y1':q_sim, 'y2':data['Rainfall'], 'y3':data['ActualET']}  
source2 = ColumnDataSource(datatable1)                                                        # Setting up Data Table ; Mapping using ColumnDataSource
columns = [TableColumn(field= 'x', title= 'Time (h)'),
        TableColumn(field= 'y', title="Qrec (m3/h)"),
        TableColumn(field= 'y1', title="Qsim (m3/h)"),
        TableColumn(field= 'y2', title="Rainfall (mm)"),
        TableColumn(field= 'y3', title="Evapotranspiration (mm)")]
                                                                                                  # Create Heading for Data Table
heading_dis = Div(text="<font color ='#808080'><h4> Data Table </h4></font><br><br>",\
              width = 800, height = 4)
data_table1 = DataTable(source=source2, columns=columns, width=580, height=150) 

# NSE
datatest = dict(
        ErrorIndicator =['NSE', 'RMSE'],
        measurement=[str(NSE), str(RMSE)],
    )
source = ColumnDataSource(datatest)                                             # Creating Error Table

columns = [
        TableColumn(field="ErrorIndicator", title= 'Error Indicator'),
        TableColumn(field="measurement", title="Measurement")]
data_table = DataTable(source=source, columns=columns, width=250, height=120)

heading_error = Div(text="<font color ='#808080'><h4> Error Measurement </h4></font><br><br>",\
              width = 250, height = 10)                                         # Heading for Error Table


# Run Model 
RM_title = Div(text="<font color ='#808080'><h4> Simulation </h4></font>",\
              width = 400, height = 2)                                          # Heading for Run Simulation
w_runmodel = Button(label='Run Model', button_type="primary")                   # Set up Run Model Button
w_runmodel.on_click(runModel)                                                   # Linking Run Model Button to runModel function


# Calibrate Model
w_calibrate = Button(label='Calibrate', button_type="warning")                  # Set up Calibration Button
w_calibrate.on_click(calibrateModel)
C_title = Div(text="<font color ='#808080'><h4> Calibration </h4></font>",\
              width = 400, height = 2)                                          # Create heading for Calibration
spacing1 = Div(text="<font color ='#808080'><h1> </h1></font>",\
              width = 400, height = 9)
spacing2 = Div(text="<font color ='#808080'><h3> </h3></font>",\
              width = 400, height = 1)
spacing3 = Div(text="<font color ='#808080'><h3> </h3></font>",\
              width = 400, height = 1)
spacing4 = Div(text="<font color ='#808080'><h1> </h1></font>",\
              width = 800, height = 175)
spacing5 = Div(text="<font color ='#808080'><h1> </h1></font>",\
              width = 400, height = 9)
spacing6 = Div(text="<font color ='#808080'><h1> </h1></font>",\
              width = 400, height = 3)
heading2 = Div(text="<font color ='#808080'><h4> Parameters </h4></font>",\
              width = 800, height = 20)

# Parameter Table
index_para = ['k1','k2','k3','k4','d1','d2','rfcf','ecorr', 'extra']            # *Bug in Bokeh that needs extra item to display the 8th para
para_table = [0,0,0,0,0,0,0,0,0]
para_formatted = []
datatable2 = dict(x=index_para,y=para_table)                                     # Map data to table using ColumnDataSource
source3 = ColumnDataSource(datatable2)

columns = [TableColumn(field= 'x', title= 'Parameter'),
        TableColumn(field= 'y', title="Calibrated Value")]

heading_para = Div(text="<font color ='#808080'><h4> Calibrated Parameters </h4></font><br><br>",\
              width = 800, height = 4)                                            # Set up heading for parameters

data_table2 = DataTable(source=source3, columns=columns, width=300, height=120)  # Set up data table
#export_table= Button(label='Export Table', button_type="default")                # Create export table button
#export_table.on_click(exportParam)                                               # Export Function

#                                  Layout       
widgetrow1 = widgetbox(spacing4, w_loadinput)
widgetcol2 = widgetbox(w_k1,w_k2,w_k3,w_k4,w_loadpara)
widgetcol3 = widgetbox(w_d1,w_d2,w_rfcf,w_ecorr)#,w_savepara)
widget7 = widgetbox(heading_dis,data_table1,w_fn,spacing6,heading2)
widget5 = widgetbox(C_title,spacing2,spacing1,w_calibrate,heading_para,data_table2)#,export_table)
widget6 = widgetbox(RM_title,spacing3,spacing5, w_runmodel,heading_error, data_table)
r=row(heading)
g = gridplot([[widget7,widgetrow1,prain],[widgetcol2,widgetcol3,pdischarge],[widget6,widget5,pstorage]])
w = column(r, g)
curdoc().add_root(w)
curdoc().title = "Sugawara GUI_sample1"

