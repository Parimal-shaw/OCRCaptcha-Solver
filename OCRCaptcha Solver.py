from burp import IBurpExtender,ITab, IHttpListener ,IContextMenuFactory, IExtensionStateListener,IMessageEditorTabFactory,IMessageEditorTab
from javax.swing import JMenuItem
from java.util import ArrayList
from java.awt import BorderLayout,  FlowLayout, Dimension
from javax.swing import JPanel, JTextArea, JScrollPane, JLabel,JRadioButton,JCheckBox, ButtonGroup,BoxLayout,JTextField, JTextArea, JScrollPane
import sys
import json
sys.path.append("./PyOCR")
from image_process import extract_img




class BurpExtender(IBurpExtender, ITab ,IHttpListener,IContextMenuFactory, IMessageEditorTabFactory,IExtensionStateListener):
    def registerExtenderCallbacks(self, callbacks):
        """
        This method is invoked when the extension is loaded.
        """
        # Set up callbacks
        self._callbacks = callbacks
        self._helpers = callbacks.getHelpers()
        

        # Set the extension name
        callbacks.setExtensionName("Py-Ocr")
        
        self._main_panel = JPanel(BorderLayout())   

        radio_button_label = JLabel("Enable or Disable the Extension:")
        checkbox_label = JLabel("Select Tools to Operate:")
        
        # Create a radio button for enabling/disabling the extension
        self.on_radio_button = JRadioButton("On")
        self.off_radio_button = JRadioButton("Off")

        radio_button_group = ButtonGroup()
        radio_button_group.add(self.on_radio_button)
        radio_button_group.add(self.off_radio_button)

        # Create checkboxes to operate individually for each tool
        self.scanner_checkbox = JCheckBox("Scanner")
        self.repeater_checkbox = JCheckBox("Repeater")
        self.intruder_checkbox = JCheckBox("Intruder")
        
                

        # Create a panel for the radio button
        radio_panel = JPanel(FlowLayout(FlowLayout.LEFT))
        radio_panel.add(self.on_radio_button)
        radio_panel.add(self.off_radio_button)
        
        radio_labels = JPanel(FlowLayout(FlowLayout.LEFT))
        radio_labels.add(radio_button_label)


        # Create a panel for the checkboxes
        checkbox_panel = JPanel(FlowLayout(FlowLayout.LEFT))
        checkbox_panel.add(self.scanner_checkbox)
        checkbox_panel.add(self.repeater_checkbox)
        checkbox_panel.add(self.intruder_checkbox)
        
        checkbox_labels = JPanel(FlowLayout(FlowLayout.LEFT))
        checkbox_labels.add(checkbox_label)
        
        #Text area
        req_text_area = JLabel("Request For Captcha Extraction")
        in_req_text_area = JLabel("Request For Captcha Insertion")
        para_text_area = JLabel("Enter Captcha Parameter Name :")
        # Create a small text box above the text area
        
        self.small_text_field = JTextField(10)  # 20 columns wide
        self.small_text_field.setEditable(True)  # Make it editable, you can set it False if you want it non-editable
        self.small_text_field.setText("captcha_parameter")
        
        # Create a non-editable text area
        self.request_text_area = JTextArea(10, 20)
        self.request_text_area.setLineWrap(True)
        self.request_text_area.setWrapStyleWord(True)
        self.request_text_area.setEditable(False)  # Make it read-only
        
        self.in_request_text_area = JTextArea(10, 20)
        self.in_request_text_area.setLineWrap(True)
        self.in_request_text_area.setWrapStyleWord(True)
        self.in_request_text_area.setEditable(False)  # Make it read-only
        
        # Add the text area to a scroll pane
        scroll_pane = JScrollPane(self.request_text_area)
        n_scroll_pane = JScrollPane(self.in_request_text_area)
        scroll_pane.setPreferredSize(Dimension(600, 450))  # Adjust size as needed
        n_scroll_pane.setPreferredSize(Dimension(600, 450))
        
        #parameter name
        small_text_box = JPanel(FlowLayout(FlowLayout.CENTER))
        small_text_box.add(para_text_area)
        small_text_box.add(self.small_text_field)
        
        #text are UI pannel
        text_area_panel = JPanel(FlowLayout(FlowLayout.LEFT,10,5))
        text_area_panel.add(scroll_pane)
        text_area_panel.add(n_scroll_pane)
        
        text_area_panel_jlabel = JPanel(FlowLayout(FlowLayout.LEFT,250,5))
        text_area_panel_jlabel.add(req_text_area)
        text_area_panel_jlabel.add(in_req_text_area)
        
        #Main UI Declaration 
        # Create a container panel for labels, radio buttons, and checkboxes
        empty_panel = JPanel()
        empty_panel.setPreferredSize(Dimension(25, 25))
        n_empty_panel = JPanel()
        n_empty_panel.setPreferredSize(Dimension(25, 25))
        m_empty_panel = JPanel()
        m_empty_panel.setPreferredSize(Dimension(25, 25))
        control_panel = JPanel()
        control_panel.setLayout(BoxLayout(control_panel, BoxLayout.Y_AXIS)) # Vertical alignment
        control_panel.add(empty_panel)
        control_panel.add(radio_labels)
        control_panel.add(radio_panel)
        control_panel.add(n_empty_panel)
        control_panel.add(checkbox_labels)
        control_panel.add(checkbox_panel)
        control_panel.add(m_empty_panel)
        control_panel.add(text_area_panel_jlabel)
        control_panel.add(text_area_panel)
        control_panel.add(small_text_box)

        # Add the control panel to the main panel
        self._main_panel.add(control_panel, BorderLayout.NORTH)
        
        callbacks.addSuiteTab(self)
        
        # Register as an HTTP listener
        callbacks.registerHttpListener(self)
        callbacks.registerMessageEditorTabFactory(self)
        callbacks.registerExtensionStateListener(self)
        self._callbacks.registerContextMenuFactory(self)
        
        self._target_endpoint = ""
        self._edit_next_request = False
        self._ocr_value = None
        self.captcha_parameter = ""
        print("Extension Loaded Succesfully")

    def createMenuItems(self, invocation):
        menu = ArrayList()
        menu.add(JMenuItem("Set As Captcha Extractor Endpoint", actionPerformed=lambda x: self.send_to_extraction(invocation)))
        menu.add(JMenuItem("Set As Captcha Insertion Endpoint", actionPerformed=lambda x: self.send_to_insertion(invocation)))
        return menu

    def send_to_extraction(self, invocation):
        # Get selected HTTP messages
        messages = invocation.getSelectedMessages()
        if not messages:
            print("No messages selected.")
            return

        for messageInfo in messages:
            # Extract request details
            request = messageInfo.getRequest()
            request_info = self._helpers.analyzeRequest(messageInfo)
            headers = request_info.getHeaders()
            body = request[request_info.getBodyOffset():].tostring()
            url = str(request_info.getUrl())
            self._target_endpoint = url
            formatted_request = "\n".join(headers) + "\n\n" + body
            self.request_text_area.setText(str(formatted_request))

    def send_to_insertion(self, invocation):
        # Get selected HTTP messages
        messages = invocation.getSelectedMessages()
        if not messages:
            print("No messages selected.")
            return

        for messageInfo in messages:
            # Extract request details
            request = messageInfo.getRequest()
            request_info = self._helpers.analyzeRequest(messageInfo)
            headers = request_info.getHeaders()
            body = request[request_info.getBodyOffset():].tostring()
            url = str(request_info.getUrl())
            self._target_endpoint = url
            formatted_request = "\n".join(headers) + "\n\n" + body
            self.in_request_text_area.setText(str(formatted_request))


    def processHttpMessage(self, toolFlag, messageIsRequest, messageInfo):
        if self.on_radio_button.isSelected():
            if not messageIsRequest and self._target_endpoint in str(self._helpers.analyzeRequest(messageInfo).getUrl()):
                        response = messageInfo.getResponse()
                        analyzed_response = self._helpers.analyzeResponse(response)
                        body_offset = analyzed_response.getBodyOffset()
                        body = response[body_offset:].tostring()
                        self._edit_next_request = True
                        ocr_value = extract_img(body)
                        self._ocr_value = ocr_value
                    
            elif messageIsRequest and self._edit_next_request:
                    self._edit_next_request = False

                # Check if the tool is Scanner, Repeater, or Intruder
                    if toolFlag in [self._callbacks.TOOL_INTRUDER] and self.intruder_checkbox.isSelected():
                        self._process_request(messageInfo)
                    elif toolFlag in [self._callbacks.TOOL_REPEATER] and self.repeater_checkbox.isSelected():
                        self._process_request(messageInfo)
                    elif toolFlag in [self._callbacks.TOOL_SCANNER] and self.scanner_checkbox.isSelected():
                        self._process_request(messageInfo)
                    else:
                        print("No Options Was Selected")

        elif self.off_radio_button.isSelected():
            print("OFF Button is Selected")
            
        else:
            print("No Button is Selected")               

    def _process_request(self, messageInfo):
                    # Modify the request
                    request = messageInfo.getRequest()
                    request_info = self._helpers.analyzeRequest(request)
                    headers = request_info.getHeaders()
                    n_body = request[request_info.getBodyOffset():].tostring()
                    parameters = request_info.getParameters()
                        
                    # Check if the content type is application/json
                    content_type = None
                    for header in headers:
                        if header.lower().startswith("content-type:"):
                            content_type = header.split(":")[1].strip().lower()
                            break
                        
                    if content_type == "application/json":
                        json_data = json.loads(n_body)
                        captcha_parameter = self.small_text_field.getText()
                        if captcha_parameter in json_data:
                            old_value = json_data[captcha_parameter]
                            ocr_value = self._ocr_value
                            ocr_value = ocr_value.replace("\r\n", "")
                            if ocr_value:
                                # Modify the value in the JSON data
                                json_data[captcha_parameter] = ocr_value
                                modified_body = json.dumps(json_data)
                            else:
                                print("Failed to extract OCR value.")
                        else:
                            print("Captcha parameter "+captcha_parameter+" not found in JSON data.")
                        
                    else:    
                        captcha_parameter = self.small_text_field.getText()
                        modified_body = n_body
                        for parameter in parameters:
                            if parameter.getName() == captcha_parameter:
                                old_value = parameter.getValue()
                                ocr_value = self._ocr_value
                                if ocr_value:
                                    new_value = ocr_value
                                    n_body = n_body.replace("\r\n", "").replace("\r", "")
                                    modified_body = n_body.replace(parameter.getName() + "=" + old_value, parameter.getName() + "=" + new_value).strip()
                                    modified_body = modified_body.replace("\r\n", "").replace("\r", "")
                                else:
                                    print("Failed to extract OCR value.")
                    new_request = self._helpers.buildHttpMessage(headers, modified_body)
                    messageInfo.setRequest(new_request)
                    self._ocr_value = None
    
    def createNewInstance(self, controller, editable):
        """
        This method is called for each new message to create a custom tab.
        """
        # Return an instance of the custom message editor tab
        return CustomResponseTab(self._callbacks, self._helpers, controller)


    def getTabCaption(self):
        """
        Returns the title of the custom tab.
        """
        return "OCRCaptcha Solver"

    def getUiComponent(self):
        """
        Returns the UI component to be displayed in the custom tab.
        """
        return self._main_panel
    
    def extensionUnloaded(self):
        print("Extension has been unloaded.")


class CustomResponseTab(IMessageEditorTab):
    def __init__(self, callbacks, helpers, controller):
        """
        Initialize the custom response tab.
        """
        self._helpers = helpers
        self._controller = controller
        
        # Create a text editor instance to display data
        self._text_editor = callbacks.createTextEditor()
        self._text_editor.setEditable(False)  # Make the tab read-only

    def getTabCaption(self):
        """
        Returns the title of the custom tab.
        """
        return "OCRCaptcha Solver"

    def getUiComponent(self):
        """
        Returns the UI component for the tab.
        """
        return self._text_editor.getComponent()
    def isEnabled(self, content, isRequest):
        """
        Determines whether the tab should be enabled for the current message.
        """
        # Enable the tab only for responses
        return not isRequest

    def setMessage(self, content, isRequest):
        """
        Sets the content of the custom tab for the current message.
        """
        if content and not isRequest:
            # Analyze the response and extract the body
            analyzed_response = self._helpers.analyzeResponse(content)
            body = content[analyzed_response.getBodyOffset():]
            n_body= body.tostring()
            self._text_editor.setText("Captcha_Value: "+extract_img(n_body))
        else:
            # Clear the editor if no content or it's a request
            self._text_editor.setText(None)

    def getMessage(self):
        """
        Returns the currently displayed message.
        """
        return self._text_editor.getText()

    def isModified(self):
        """
        Indicates whether the content has been modified.
        """
        return False

    def getSelectedData(self):
        """
        Returns the currently selected data in the tab.
        """
        return self._text_editor.getSelectedText()