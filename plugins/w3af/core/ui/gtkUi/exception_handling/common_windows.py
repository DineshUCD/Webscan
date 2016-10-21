'''
common_windows_report.py

Copyright 2012 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

'''
import gtk
import Queue
import threading
import gobject

from core.controllers.easy_contribution.sourceforge import SourceforgeXMLRPC
from core.controllers.easy_contribution.sourceforge import DEFAULT_USER_NAME, DEFAULT_PASSWD

from core.ui.gtkUi.helpers import endThreads
from core.ui.gtkUi.entries import EmailEntry
from core.ui.gtkUi.helpers import Throbber
from core.ui.gtkUi.constants import W3AF_ICON



class simple_base_window(gtk.Window):

    def __init__(self, type=gtk.WINDOW_TOPLEVEL):
        '''
        One simple class to create other windows.
        '''
        super(simple_base_window,self).__init__(type=type)    
        
        self.connect("delete-event", gtk.main_quit)
        self.set_icon_from_file(W3AF_ICON)
        
    def _handle_cancel(self, widg):
        endThreads()
        self.destroy()


class bug_report_worker(threading.Thread):
    '''
    The simplest threading object possible to report bugs to the network without
    blocking the UI.
    '''
    FINISHED = -1
    
    def __init__(self, bug_report_function, bugs_to_report):
        threading.Thread.__init__(self)
        self.bug_report_function = bug_report_function
        self.bugs_to_report = bugs_to_report
        self.output = Queue.Queue()

    def run(self):
        '''
        The thread's main method, where all the magic happens.
        '''
        for bug in self.bugs_to_report:
            result = apply(self.bug_report_function, bug)
            self.output.put(result)
        
        self.output.put(self.FINISHED)


class report_bug_show_result(gtk.MessageDialog):
    '''
    A class that shows the result of one or more bug reports to the user. The
    window shows a "Thanks" message and links to the bugs that were generated.
    
    Unlike previous versions, this window actually sends the bugs to the network
    since we want to show the ticket IDs "in real time" to the user instead of
    reporting them all and then showing a long list of items.
    '''
    
    def __init__(self, bug_report_function, bugs_to_report):
        '''
        @param bug_report_function: The function that's used to report bugs.
                                    apply(bug_report_function, bug_to_report)
                                    
        @param bugs_to_report: An iterable with the bugs to report. These are
                               going to be the parameters for the bug_report_function.
        '''
        gtk.MessageDialog.__init__(self,
                                   None,
                                   gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                                   gtk.MESSAGE_INFO,
                                   gtk.BUTTONS_OK,
                                   None)
        
        self.bug_report_function = bug_report_function
        self.bugs_to_report = bugs_to_report
        self.ticket_ids_in_markup = 0
        self.reported_ids = []
        
        self.set_title('Bug report results')
        self.set_icon_from_file(W3AF_ICON)

        # Disable OK button until the worker finishes the bug reporting process
        ok_button = self.get_widget_for_response(gtk.RESPONSE_OK)
        ok_button.set_sensitive(False)
        
        
    def run(self):
        #
        #    Main text
        #
        text = 'Thank you for reporting your bugs, it helps us improve our'
        text += ' scanning engine. If you want to get involved with the project'
        text += ' please send an email to our <a href="mailto:%s">mailing list</a>.'
        text = text % ('w3af-develop@lists.sourceforge.net')
        # All these lines are here to add a label instead of the easy "set_markup"
        # in order to avoid a bug where the label text appears selected
        msg_area = self.get_message_area()
        [msg_area.remove(c) for c in msg_area.get_children()]
        label = gtk.Label()
        label.set_markup( text )
        label.set_line_wrap(True)
        label.select_region(0, 0)
        msg_area.pack_start(label)
        

        self.worker = bug_report_worker(self.bug_report_function, self.bugs_to_report)
        self.worker.start()        
        gobject.timeout_add(200, self.add_result_from_worker)
        
        self.status_hbox = gtk.HBox()
        
        #
        #    Empty markup for the ticket ids
        #
        self.link_label = gtk.Label( '' )
        self.link_label.set_line_wrap(True)
        self.link_label.set_use_markup( True )
        self.status_hbox.pack_end(self.link_label)
        
        #
        #    Throbber, only show while still running.
        #
        
        self.throbber = Throbber()
        self.throbber.running(True)
        self.status_hbox.pack_end(self.throbber)
        
        #
        #    Check, hidden at the beginning 
        #    http://www.pygtk.org/docs/pygtk/gtk-stock-items.html
        #
        self.done_icon = gtk.Image()
        self.done_icon.set_from_stock(gtk.STOCK_YES, gtk.ICON_SIZE_BUTTON)
        self.status_hbox.pack_end(self.done_icon)
        
        self.vbox.pack_start(self.status_hbox, True, True)

        self.add(self.vbox)
        self.show_all()
        self.done_icon.hide()
        
        super(report_bug_show_result, self).run()
        self.destroy()
        
        return self.reported_ids
        
      
    def add_result_from_worker(self):
        '''
        Adds the results from the worker to the text that's shown in the window
        '''
        # The links to the reported tickets
        try:
            bug_report_result = self.worker.output.get(block=False)
        except Queue.Empty:
            # The worker is reporting stuff to the network and doesn't
            # have any results at this moment. Call me in some seconds.
            return True
        
        if bug_report_result == self.worker.FINISHED:
            self.throbber.running(False)
            self.throbber.hide()
            self.done_icon.show()
            ok_button = self.get_widget_for_response(gtk.RESPONSE_OK)
            ok_button.set_sensitive(True)
            # don't call me anymore !
            return False
        else:
            # Add the data to the label and ask to be called again
            ticket_id, ticket_url = bug_report_result
            self.add_link(ticket_id, ticket_url)
            return True

    def add_link(self, ticket_id, ticket_url):
        self.reported_ids.append(ticket_id)
        
        new_link = '<a href="%s">%s</a>'
        new_link = new_link % (ticket_url, ticket_id)
        
        current_markup = self.link_label.get_label()

        needs_new_line = False
        if self.ticket_ids_in_markup == 4:
            needs_new_line = True
            self.ticket_ids_in_markup = 0
        else:
            self.ticket_ids_in_markup += 1

        needs_delim = True
        if len(current_markup) == 0 or needs_new_line:
            needs_delim = False
                    
        current_markup += ('\n' if needs_new_line else '') + (', ' if needs_delim else '')
        current_markup += new_link
        
        self.link_label.set_markup(current_markup)


class dlg_ask_credentials(gtk.MessageDialog):
    '''
    A dialog that allows any exception handler to ask the user for his credentials
    before sending any bug report information to the network. The supported types
    of credentials are:
    
        * Anonymous
        * Email
        * Sourceforge user (soon to be deprecated, nobody uses it).
    
    '''

    METHOD_ANON = 1
    METHOD_EMAIL = 2
    METHOD_SF = 3

    def __init__(self, invalid_login=False):
        '''
        @return: A tuple with the following information:
                    (method, params)
                
                Where method is one of METHOD_ANON, METHOD_EMAIL, METHOD_SF and,
                params is the email or the sourceforge username and password,
                in the anon case, the params are empty.
        '''
        gtk.MessageDialog.__init__(self,
                                   None,
                                   gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                                   gtk.MESSAGE_QUESTION,
                                   gtk.BUTTONS_OK,
                                   None)
        
        self._invalid_login = invalid_login
        
        self.set_icon_from_file(W3AF_ICON)
        self.set_title('Bug report method - Step 1/2')
        
    
    def run(self):
        '''
        Setup the dialog and return the results to the invoker.
        '''
        
        msg = '\nChoose how to report the bug(s)'
        
        if self._invalid_login:
            msg += '<b><i>Invalid credentials, please try again.</i></b>\n\n'
        
        self.set_markup( msg )
    
        #
        #    Anon
        #
        anon_button = gtk.RadioButton(None, "Anonymously")
        anon_button.set_active(True)
        self.vbox.pack_start(anon_button, True, True, 0)
    
        separator = gtk.HSeparator()
        self.vbox.pack_start(separator, True, True, 0)
        
        #
        #    Email
        #
        email_button = gtk.RadioButton(anon_button, "Use email address")
        self.vbox.pack_start(email_button, True, True, 0)
        
        # Create the text input field
        self.email_entry = EmailEntry(self._email_entry_changed)
        self.email_entry.connect("activate", lambda x: self.response(gtk.RESPONSE_OK))  
        
        # Create a horizontal box to pack the entry and a label
        email_hbox = gtk.HBox()
        email_hbox.pack_start(gtk.Label("Email address:"), False, 5, 5)
        email_hbox.pack_end(self.email_entry)
        email_hbox.set_sensitive(False)
        self.vbox.pack_start(email_hbox, True, True, 0)
        
        separator = gtk.HSeparator()
        self.vbox.pack_start(separator, True, True, 0)
    
        #
        #    Sourceforge credentials
        #
        sf_button = gtk.RadioButton(email_button, "Sourceforge credentials:")
        self.vbox.pack_start(sf_button, True, True, 0)
        
        sf_vbox = gtk.VBox()
        
        # Create the text input field
        user_entry = gtk.Entry()
        user_entry.connect("activate", lambda x: self.response(gtk.RESPONSE_OK))  
    
        user_hbox = gtk.HBox()
        user_hbox.pack_start(gtk.Label("Username:  "), False, 5, 5)
        user_hbox.pack_end(user_entry)
        sf_vbox.pack_start(user_hbox, True, True, 0)
        
        # Create the password entry
        passwd_entry = gtk.Entry()
        passwd_entry.set_visibility(False)
        passwd_entry.connect("activate", lambda x: self.response(gtk.RESPONSE_OK))  
    
        passwd_hbox = gtk.HBox()
        passwd_hbox.pack_start(gtk.Label("Password:  "), False, 5, 5)
        passwd_hbox.pack_end(passwd_entry)
        sf_vbox.pack_start(passwd_hbox, True, True, 0)
        
        # Some secondary text
        warning_label = gtk.Label()
        warning = "\nYour credentials won't be stored in your computer,\n"
        warning += "  and will only be sent over HTTPS connections."
        warning_label.set_text(warning)
        sf_vbox.pack_start(warning_label, True, True, 0)
        sf_vbox.set_sensitive(False)
        self.vbox.pack_start(sf_vbox, True, True, 0)
        
        separator = gtk.HSeparator()
        self.vbox.pack_start(separator, True, True, 0)
    
        # Handling of sensitiviness between the radio contents
        anon_button.connect("toggled", self._radio_callback_anon, [], [email_hbox,sf_vbox])        
        email_button.connect("toggled", self._radio_callback_email, [email_hbox,], [sf_vbox,])
        sf_button.connect("toggled", self._radio_callback_sf, [sf_vbox,], [email_hbox,])
                
        # Go go go!        
        self.show_all()
        super(dlg_ask_credentials, self).run()
        
        #
        # Get the results, generate the result tuple and return
        #
        active_label = [r.get_label() for r in anon_button.get_group() if r.get_active()]
        active_label = active_label[0].lower()
        
        if 'email' in active_label:
            method = self.METHOD_EMAIL
            email = self.email_entry.get_text()
            params = (email,)
        elif 'sourceforge' in active_label:
            method = self.METHOD_SF
            user = user_entry.get_text()
            passwd = passwd_entry.get_text()
            params = (user, passwd)
        else:
            method = self.METHOD_ANON
            params = ()
        
        # I'm done!
        self.destroy()

        return (method, params)

    def _email_entry_changed(self, x, y):
        '''
        Disable the OK button if the email is invalid
        '''
        ok_button = self.get_widget_for_response(gtk.RESPONSE_OK)
        
        if self.email_entry.isValid():
            # Activate OK button
            ok_button.set_sensitive(True)
        else:
            # Disable OK button
            ok_button.set_sensitive(False)

    def _radio_callback_anon(self, event, enable, disable):
        self._radio_callback(event, enable, disable)
        # re-enable the button in case it was disabled by an invalid email address entry
        ok_button = self.get_widget_for_response(gtk.RESPONSE_OK)
        ok_button.set_sensitive(True)

    def _radio_callback_email(self, event, enable, disable):
        self._radio_callback(event, enable, disable)
        self._email_entry_changed(True,True)

    def _radio_callback_sf(self, event, enable, disable):
        self._radio_callback(event, enable, disable)
        # re-enable the button in case it was disabled by an invalid email address entry
        ok_button = self.get_widget_for_response(gtk.RESPONSE_OK)
        ok_button.set_sensitive(True)

    def _radio_callback(self, event, enable, disable):
        '''
        Handle the clicks on the different radio buttons.
        '''
        for section in enable:
            section.set_sensitive(True)

        for section in disable:
            section.set_sensitive(False)


class dlg_ask_bug_info(gtk.MessageDialog):
    
    def __init__(self, invalid_login=False):
        '''
        @return: A tuple with the following information:
                    (bug_summary, bug_description)
                
        '''
        gtk.MessageDialog.__init__(self,
                                   None,
                                   gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                                   gtk.MESSAGE_QUESTION,
                                   gtk.BUTTONS_OK,
                                   None)
        
        self.set_icon_from_file(W3AF_ICON)
        self.set_title('Bug information - Step 2/2')

    def run(self):
            
        default_text = '''What steps will reproduce the problem?
1. 
2. 
3. 

What is the expected output? What do you see instead?


What operating system are you using?


Please provide any additional information below:


'''
        
        msg = 'Please provide the following information about the bug\n'
        self.set_markup( msg )
        
        #create the text input field
        summary_entry = gtk.Entry()
        
        sw = gtk.ScrolledWindow()
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        description_text_view = gtk.TextView()
        description_text_view.set_size_request(240, 300)
        description_text_view.set_wrap_mode(gtk.WRAP_WORD)
        buffer = description_text_view.get_buffer()
        buffer.set_text(default_text)
        sw.add(description_text_view)
        
        #create a horizontal box to pack the entry and a label
        summary_hbox = gtk.HBox()
        summary_hbox.pack_start(gtk.Label("Summary    "), False, 5, 5)
        summary_hbox.pack_end(summary_entry)
        
        description_hbox = gtk.HBox()
        description_hbox.pack_start(gtk.Label("Description"), False, 5, 5)
        description_hbox.pack_start(sw, True, True, 0)
        
        #add it and show it
        self.vbox.pack_start(summary_hbox, True, True, 0)
        self.vbox.pack_start(description_hbox, True, True, 0)
        self.show_all()
        
        # Go go go
        super(dlg_ask_bug_info, self).run()
        
        summary = summary_entry.get_text()
        description = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter())
        
        self.destroy()
        
        return summary, description

class trac_bug_report(object):
    '''
    Class that models user interaction with Trac to report ONE bug.
    '''
    
    def __init__(self, tback='', fname=None, plugins=''):
        self.sf = None
        self.tback = tback
        self.fname = fname
        self.plugins = plugins
        self.autogen = False
    
    def report_bug(self):
        sf, summary, userdesc, email = self._info_and_login()
        rbsr = report_bug_show_result( self._report_bug_to_sf, [(sf, summary, userdesc, email),] )
        rbsr.run()
    
    def _info_and_login(self):
        # Do the login
        sf, email = self._login_sf()
        
        # Ask for a bug title and description
        dlg_bug_info = dlg_ask_bug_info()
        summary, userdesc = dlg_bug_info.run()
        
        return sf, summary, userdesc, email
        
    def _report_bug_to_sf(self, sf, summary, userdesc, email):
        '''
        Send bug to Trac.
        '''
        try:
            ticket_url, ticket_id = sf.report_bug(summary, userdesc, self.tback,
                                                  self.fname, self.plugins, self.autogen,
                                                  email)
        except:
            return None, None
        else:
            return ticket_url, ticket_id
    
    def _login_sf(self, retry=3):
        '''
        Perform user login.
        '''
        invalid_login = False
        email = None
        
        while retry:
            # Decrement retry counter
            retry -= 1
            # Ask for user and password, or anonymous
            dlg_cred = dlg_ask_credentials(invalid_login)
            method, params = dlg_cred.run()
            dlg_cred.destroy()
            
            if method == dlg_ask_credentials.METHOD_SF:
                user, password = params
            
            elif method == dlg_ask_credentials.METHOD_EMAIL:
                # The user chose METHOD_ANON or METHOD_EMAIL with both these
                # methods the framework actually logs in using our default 
                # credentials
                user, password = (DEFAULT_USER_NAME, DEFAULT_PASSWD)
                email = params[0]

            else:
                # The user chose METHOD_ANON or METHOD_EMAIL with both these
                # methods the framework actually logs in using our default 
                # credentials
                user, password = (DEFAULT_USER_NAME, DEFAULT_PASSWD)
            
            sf = SourceforgeXMLRPC(user, password)
            login_result = sf.login()
            invalid_login = not login_result
            
            if login_result:
                break
            
        return (sf, email)

class trac_multi_bug_report(trac_bug_report):
    '''
    Class that models user interaction with Trac to report ONE or MORE bugs.
    '''
    
    def __init__(self, exception_list, scan_id):
        trac_bug_report.__init__(self)
        self.sf = None
        self.exception_list = exception_list
        self.scan_id = scan_id
        self.autogen = False
    
    def report_bug(self):
        sf, email = self._login_sf()
        
        bug_info_list = []
        for edata in self.exception_list:
            tback = edata.get_details()
            plugins = edata.enabled_plugins
            bug_info_list.append( (sf, tback, self.scan_id, email, plugins) )
            
        rbsr = report_bug_show_result( self._report_bug_to_sf, bug_info_list )
        rbsr.run()
    
    def _report_bug_to_sf(self, sf, tback, scan_id, email, plugins):
        '''
        Send bug to Trac.
        '''
        userdesc = 'No user description was provided for this bug report given'
        userdesc += ' that it was related to handled exceptions in scan with id'
        userdesc += ' %s' % scan_id
        try:
            ticket_url, ticket_id = sf.report_bug(None, userdesc, tback=tback,
                                                  plugins=plugins, 
                                                  autogen=self.autogen,
                                                  email=email)
        except:
            return None, None
        else:
            return ticket_url, ticket_id
