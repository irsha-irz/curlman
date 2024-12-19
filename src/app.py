import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import requests
import json
import mimetypes
import os

class CurlAssistant:
    def __init__(self, root):
        self.root = root
        self.root.title("Curl Assistant")
        self.collections = {}
        self.variables = {}
        self.headers = {}
        self.query_params = {}
        self.collections = {}
        self.current_collection = None
        self.load_data()
        # Layout
        self.create_main_frame()
        self.create_variable_manager()
        self.create_response_viewer()
        self.query_params_frame = ttk.LabelFrame(self.main_frame, text="Query Parameters")
        self.query_params_frame.pack(fill=tk.BOTH, expand=True)
        self.query_params_tree = ttk.Treeview(self.query_params_frame, columns=("Key", "Value"), show="headings")
        self.query_params_tree.heading("Key", text="Key")
        self.query_params_tree.heading("Value", text="Value")
        self.query_params_tree.pack(fill=tk.BOTH, expand=True)
        # Load collections from file
        # self.load_collection()
        # Dropdown for collections
        self.collection_label = ttk.Label(root, text="Select Collection:")
        self.collection_label.pack(pady=5)
        self.collection_dropdown = ttk.Combobox(root, state="readonly")
        self.collection_dropdown.pack(pady=5)
        self.collection_dropdown.bind("<<ComboboxSelected>>", self.on_collection_selected)
        self.create_collection_btn = tk.Button(root, text="Create Collection", command=self.create_collection)
        self.create_collection_btn.pack(pady=5)
        # Listbox for requests in the selected collection
        self.requests_label = ttk.Label(root, text="Requests in Collection:")
        self.requests_label.pack(pady=5)
        self.requests_listbox = tk.Listbox(root, height=10)
        self.requests_listbox.pack(pady=5)
        self.requests_listbox.bind("<<ListboxSelect>>", self.load_collection)
        # Populate dropdown
        self.update_collection_dropdown()

    def create_main_frame(self):
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        # URL and Method Entry Field
        request_frame = tk.Frame(self.main_frame)
        request_frame.pack(fill=tk.X, padx=5, pady=5)
        # Dropdown for HTTP Method
        tk.Label(request_frame, text="Method:").pack(side=tk.LEFT, padx=5)
        self.method_var = tk.StringVar(value="GET")
        self.method_menu = ttk.Combobox(request_frame, textvariable=self.method_var, values=["GET", "POST", "PUT", "DELETE", "PATCH"])
        self.method_menu.pack(side=tk.LEFT, padx=5)
        # URL Entry Field
        tk.Label(request_frame, text="URL:").pack(side=tk.LEFT, padx=5)
        self.url_entry = tk.Entry(request_frame)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        # Tabs
        self.tabs = ttk.Notebook(self.main_frame)
        self.tabs.pack(fill=tk.BOTH, expand=True)
        self.headers_tab = self.create_tab("Headers", self.headers)
        self.query_params_tab = self.create_tab("Query Params", self.query_params)
        self.body_tab = self.create_body_tab()
        # Execute and Save Buttons
        button_frame = tk.Frame(self.main_frame)
        button_frame.pack(pady=10)
        self.execute_btn = tk.Button(button_frame, text="Execute", command=self.execute_request)
        self.execute_btn.pack(side=tk.LEFT, padx=5)
        self.save_request_btn = tk.Button(button_frame, text="Save Request", command=self.save_request)
        self.save_request_btn.pack(side=tk.LEFT, padx=5)

    def create_tab(self, name, data_store):
        tab = ttk.Frame(self.tabs)
        self.tabs.add(tab, text=name)
        # Treeview for key-value pairs
        columns = ("Key", "Value")
        tree = ttk.Treeview(tab, columns=columns, show="headings")
        tree.heading("Key", text="Key")
        tree.heading("Value", text="Value")
        tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        # Buttons for adding, editing, and deleting rows
        button_frame = tk.Frame(tab)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        add_btn = tk.Button(button_frame, text="Add", command=lambda: self.add_row(tree, data_store))
        add_btn.pack(side=tk.LEFT, padx=5)
        edit_btn = tk.Button(button_frame, text="Edit", command=lambda: self.edit_row(tree, data_store))
        edit_btn.pack(side=tk.LEFT, padx=5)
        delete_btn = tk.Button(button_frame, text="Delete", command=lambda: self.delete_row(tree, data_store))
        delete_btn.pack(side=tk.LEFT, padx=5)
        # Store treeview reference
        setattr(self, f"{name.lower()}_tree", tree)
        return tab

    def create_body_tab(self):
        tab = ttk.Frame(self.tabs)
        self.tabs.add(tab, text="Body")
        self.body_type_var = tk.StringVar(value="JSON")
        self.body_type_menu = ttk.Combobox(tab, textvariable=self.body_type_var, values=["JSON", "Form-Data", "Raw"])
        self.body_type_menu.pack(pady=5)
        self.body_text = tk.Text(tab, height=10)
        self.body_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        return tab

    def create_variable_manager(self):
        self.variables_tab = ttk.Frame(self.tabs)
        self.tabs.add(self.variables_tab, text="Variables")
        self.var_listbox = tk.Listbox(self.variables_tab)
        self.var_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.var_entry = tk.Entry(self.variables_tab)
        self.var_entry.pack(padx=5, pady=5)
        self.add_var_btn = tk.Button(self.variables_tab, text="Add Variable", command=self.add_variable)
        self.add_var_btn.pack(pady=5)

    def create_response_viewer(self):
        response_frame = tk.Frame(self.main_frame)
        response_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.response_tabs = ttk.Notebook(response_frame)
        self.response_tabs.pack(fill=tk.BOTH, expand=True)
        self.response_header_tab = ttk.Frame(self.response_tabs)
        self.response_tabs.add(self.response_header_tab, text="Headers")
        self.response_header_text = tk.Text(self.response_header_tab, wrap="word", state="disabled")
        self.response_header_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.response_body_tab = ttk.Frame(self.response_tabs)
        self.response_tabs.add(self.response_body_tab, text="Body")
        self.response_body_text = tk.Text(self.response_body_tab, wrap="word", state="disabled")
        self.response_body_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.response_logs_tab = ttk.Frame(self.response_tabs)
        self.response_tabs.add(self.response_logs_tab, text="Logs")
        self.response_logs_text = tk.Text(self.response_logs_tab, wrap="word", state="disabled")
        self.response_logs_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def add_row(self, tree, data_store):
        key = simpledialog.askstring("Input", "Enter Key:")
        value = simpledialog.askstring("Input", "Enter Value:")
        if key and value:
            data_store[key] = value
            tree.insert("", tk.END, values=(key, value))

    def edit_row(self, tree, data_store):
        selected_item = tree.selection()
        if selected_item:
            item = selected_item[0]
            key, value = tree.item(item, "values")
            new_key = simpledialog.askstring("Edit", "Edit Key:", initialvalue=key)
            new_value = simpledialog.askstring("Edit", "Edit Value:", initialvalue=value)
            if new_key and new_value:
                del data_store[key]
                data_store[new_key] = new_value
                tree.item(item, values=(new_key, new_value))

    def delete_row(self, tree, data_store):
        selected_item = tree.selection()
        if selected_item:
            item = selected_item[0]
            key, _ = tree.item(item, "values")
            del data_store[key]
            tree.delete(item)

    def add_variable(self):
        variable = self.var_entry.get()
        if "=" in variable:
            key, value = variable.split("=", 1)
            self.variables[key.strip()] = value.strip()
            self.var_listbox.insert(tk.END, f"{key.strip()} = {value.strip()}")
        else:
            messagebox.showerror("Invalid Format", "Variable must be in the format: key=value")

    def update_response_viewer(self, response):
        self.response_header_text.config(state="normal")
        self.response_header_text.delete("1.0", tk.END)
        self.response_header_text.insert(tk.END, json.dumps(dict(response.headers), indent=4))
        self.response_header_text.config(state="disabled")
        self.response_body_text.config(state="normal")
        self.response_body_text.delete("1.0", tk.END)
        self.response_body_text.insert(tk.END, response.text)
        self.response_body_text.config(state="disabled")
        self.update_logs(f"Request executed successfully. Status code: {response.status_code}")

    def update_logs(self, log_message):
        self.response_logs_text.config(state="normal")
        self.response_logs_text.insert(tk.END, f"{log_message}\n")
        self.response_logs_text.config(state="disabled")
    
    def load_collections(self):
        """Load collections from a JSON file."""
        try:
            if os.path.exists("collections.json"):
                with open("collections.json", "r") as file:
                    self.collections = json.load(file)
        except json.JSONDecodeError:
            print("Error reading collections.json. Ensure it's a valid JSON file.")
            self.collections = {}

    def update_collection_dropdown(self):
        """Update the dropdown with collection names."""
        collection_names = list(self.collections.keys())
        self.collection_dropdown["values"] = collection_names
        if collection_names:
            self.collection_dropdown.current(0)  # Select the first collection by default
            self.on_collection_selected()

    def on_collection_selected(self, event=None):
        """Handle collection selection from the dropdown."""
        selected_collection = self.collection_dropdown.get()
        if selected_collection:
            self.current_collection = selected_collection
            self.update_requests_listbox(selected_collection)

    def update_requests_listbox(self, collection_name):
        """Update the listbox with requests in the selected collection."""
        self.requests_listbox.delete(0, tk.END)  # Clear existing items
        requests = self.collections.get(collection_name, {})
        for req_name in requests:
            self.requests_listbox.insert(tk.END, req_name)
	
    def load_data(self):
        """ Load collections and requests from a JSON file """
        if os.path.exists("collections.json"):
            with open("collections.json", "r") as file:
                self.collections = json.load(file)

    def save_data(self):
        """ Save collections and requests to a JSON file """
        with open("collections.json", "w") as file:
            json.dump(self.collections, file, indent=4)

    def add_collection(self):
        collection_name = simpledialog.askstring("Collection Name", "Enter collection name:")
        if collection_name:
            if collection_name not in self.collections:
                self.collections[collection_name] = {}
                self.collection_list.insert(tk.END, collection_name)
                self.save_data()

    def create_collection(self):
        """Prompt the user to create a new collection."""
        collection_name = simpledialog.askstring("Create Collection", "Enter collection name:")
        if collection_name:
            if collection_name in self.collections:
                messagebox.showerror("Error", f"Collection '{collection_name}' already exists.")
            else:
                self.collections[collection_name] = {}
                self.save_data()
                self.update_collection_dropdown()
                messagebox.showinfo("Success", f"Collection '{collection_name}' created successfully!")

    def load_collection(self, event):
        """Load the selected request's details into the main frame."""
        selected_index = self.requests_listbox.curselection()
        if selected_index:
            request_name = self.requests_listbox.get(selected_index)
            collection_name = self.collection_dropdown.get()
            if not collection_name:
                messagebox.showerror("Error", "No collection selected.")
                return
            # Get the request details
            request_details = self.collections.get(collection_name, {}).get(request_name, {})
            if request_details:
                # Populate the URL
                self.url_entry.delete(0, tk.END)
                self.url_entry.insert(0, request_details.get("url", ""))
                # Populate headers
                self.headers = request_details.get("headers", {})
                self.update_treeview(self.headers_tree, self.headers)
                # Populate query parameters
                self.query_params = request_details.get("query_params", {})
                self.update_treeview(self.query_params_tree, self.query_params)
                # Populate body
                self.body_text.delete("1.0", tk.END)
                self.body_text.insert("1.0", request_details.get("body", ""))
                # Set HTTP method
                self.method_var.set(request_details.get("method", "GET"))
                self.body_type_var.set(request_details.get("body_type", "JSON"))
                messagebox.showinfo("Request Loaded", f"Request '{request_name}' loaded successfully!")
            else:
                messagebox.showerror("Error", "Request details not found.")

    def load_requests(self, collection_name):
        """Load the first request from the selected collection into the fields."""
        collection = self.collections.get(collection_name, {})
        if collection:
            # Display a dialog or prompt to select a specific request within the collection
            request_name = simpledialog.askstring("Select Request", f"Available requests: {', '.join(collection.keys())}\nEnter request name:")
            if request_name in collection:
                request = collection[request_name]
                # Populate URL
                self.url_entry.delete(0, tk.END)
                self.url_entry.insert(0, request.get("url", ""))
                # Populate headers
                self.headers = request.get("headers", {})
                self.update_treeview(self.headers_tree, self.headers)
                # Populate query parameters
                self.query_params = request.get("query_params", {})
                self.update_treeview(self.query_params_tree, self.query_params)
                # Populate body
                self.body_text.delete("1.0", tk.END)
                self.body_text.insert("1.0", request.get("body", ""))
                # Set HTTP method
                self.method_var.set(request.get("method", "GET"))
                messagebox.showinfo("Request Loaded", f"Request '{request_name}' loaded successfully!")
            else:
                messagebox.showerror("Error", "Request not found in the collection.")
        else:
            messagebox.showerror("Error", "No requests available in this collection.")

    def update_treeview(self, tree, data_store):
        """ Update a Treeview widget with key-value pairs from a data store. """
        tree.delete(*tree.get_children())  # Clear existing rows
        for key, value in data_store.items():
            tree.insert("", tk.END, values=(key, value))

    def save_request(self):
        """Save the current request to the selected collection."""
        selected_collection = self.collection_dropdown.get()
        if not selected_collection:
            messagebox.showerror("Error", "No collection selected.")
            return
        request_name = simpledialog.askstring("Request Name", "Enter request name:")
        if request_name:
            collection = self.collections.get(selected_collection, {})
            url = self.url_entry.get()
            headers = self.headers  # Collect headers as dict
            body = self.body_text.get("1.0", "end-1c")
            query_params = self.query_params  # Collect query params as dict
            method = self.method_var.get()  # Get HTTP method
            body_type = self.body_type_var.get()
            # Save request details
            collection[request_name] = {
                "url": url,
                "headers": headers,
                "body": body,
                "query_params": query_params,
                "method": method,
                "body_type": body_type
            }
            self.save_data()
            self.update_requests_listbox(selected_collection)
            messagebox.showinfo("Saved", f"Request '{request_name}' saved successfully!")

    def execute_request(self):
        method = self.method_var.get()
        url = self.url_entry.get().strip()
        headers = self.headers
        params = self.query_params
        body_type = self.body_type_var.get()
        print(f"body_type: {body_type}")
        body = self.body_text.get("1.0", tk.END).strip()
        print(f"body: {body}")
        try:
            data = {}
            files = {}
            if body_type == "JSON":
                # Send as JSON
                json_body = json.loads(body) if body else None
                response = requests.request(method, url, headers=headers, params=params, json=json_body)
            elif body_type == "Form-Data":
                # Parse form-data body
                for line in body.splitlines():
                    if "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip()
                        if value.startswith("@"):
                            # File upload
                            file_path = value[1:]
                            file_name = file_path.rsplit('\\', 1)[-1]
                            file_extension = file_name.rsplit('.', 1)[-1]
                            print(f"file_name : {file_name}, file_extension: {file_extension}")
                            try:
                                mime_type, _ = mimetypes.guess_type(file_path)
                                print(f"mime_type: {mime_type}")
                                files[key] = (file_name, open(file_path, "rb"), mime_type or "application/octet-stream")
                            except Exception as e:
                                self.update_logs(f"Error opening file {file_path}: {e}")
                        else:
                            # Regular key-value pair
                            data[key] = value
                # Make the request with both data and files
                response = requests.request(method, url, headers=headers, params=params, data=data, files=files)
            else:
                # Send as Raw Data
                response = requests.request(method, url, headers=headers, params=params, data=body)
            self.update_response_viewer(response)
        except Exception as e:
            self.update_logs(f"Error: {str(e)}")
        finally:
            # Close any opened files
            for file in files.values():
                file[1].close()

if __name__ == "__main__":
    root = tk.Tk()
    app = CurlAssistant(root)
    root.mainloop()
