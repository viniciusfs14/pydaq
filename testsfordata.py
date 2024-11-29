def get_data_nidaq_filters(self):
       
        self.data = []
        self.data_filtered = [] # new vector to add filtered values
        self.time_var = []

        # Checking if path was defined
        self._check_path()

        # Number of self.cycles necessary
        self.cycles = int(np.floor(self.session_duration / self.ts)) + 1

        # Initializing device, with channel defined
        task = nidaqmx.Task()
        task.ai_channels.add_ai_voltage_chan(
            self.device + "/" + self.channel, terminal_config=self.terminal
        )

        if self.plot:  # If plot, start updatable plot
            self.title = f"PYDAQ - Data Acquisition. {self.device}, {self.channel}"
            self._start_updatable_plot()

        # Main loop, where data will be acquired
        for k in range(self.cycles):

            # Counting time to append data and update interface
            st = time.time()

            # Acquire data
            temp = task.read() # data original values 
            
        
            # I have to create the filter here and append temp_filtered in new data vector
            
            # Queue data in a list
            self.data.append(temp) 
            self.time_var.append(k * self.ts)

            if self.yes_ratio
            if self.plot:

                # Checking if there is still an open figure. If not, stop the
                # for loop.
                try:
                    plt.get_figlabels().index("iter_plot")
                except BaseException:
                    break

                # Updating data values
                self._update_plot(self.time_var, self.data)
                
                ## here can I plot only filtered data or can i modify to plot both data

            print(f"Iteration: {k} of {self.cycles - 1}")

            # Getting end time
            et = time.time()

            # Wait for (ts - delta_time) seconds
            try:
                time.sleep(self.ts + (st - et))
            except BaseException:
                warnings.warn(
                    "Time spent to append data and update interface was greater than ts. "
                    "You CANNOT trust time.dat"
                )

        # Closing task
        task.close()

        # Check if data will or not be saved, and save accordingly
        if self.save:
            print("\nSaving data ...")
            # Saving time_var and data
            self._save_data(self.time_var, "time.dat")
            self._save_data(self.data, "data.dat")
            print("\nData saved ...")

        return