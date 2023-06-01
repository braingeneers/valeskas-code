// This will be the object that will contain the Vue attributes
// and be used to initialize it.
let app = {};


// Given an empty app object, initializes it filling its attributes,
// creates a Vue instance, and then initializes the Vue instance.
let init = (app) => {

    // This is the Vue data.
    app.data = {
        experiment_names: [],
        experiment_name: "",
        cam_names: [],
        chosen_experiment_name: "",
        chosen_cam_name: "",
        page_size: 5,
        images: [],
        show_experiment_dropdown: false,
        show_cam_dropdown: false,
        show_count_dropdown: false,
        images_ready: false,
        loading: false,
        clicked_image: "",
        show_image_overlay: false,
        cur_img_index: 0,
        file_names: [],
        count_been_selected: false,
        cam_been_selected: false,
        experiment_been_selected: false,
        start_index: null,
        ready_to_get: false,
        old_start_index: null,
        timelapse: null,
        timelapse_ready: false,
        index_provided: false,
    };

    app.enumerate = (a) => {
        // This adds an _idx field to each element of the array.
        let k = 0;
        a.map((e) => {e._idx = k++;});
        return a;
    };

    app.update_button = function () {
        // This removes the disabled attribute on the View Images button if the required fields have been supplied.
        if (app.vue.cam_been_selected && app.vue.experiment_been_selected) {
            app.vue.ready_to_get = true;
        }
    };

    app.get_experiments = function () {
        axios.get(get_experiments_url)
            .then(function (result) {
                app.vue.experiment_names = app.enumerate(result.data.experiment_names);
            });
    }

    app.set_experiment = function (experiment_name) {
        axios.get(set_experiment_url, {params: {experiment_name: experiment_name}})
            .then(function (result) {
                app.vue.cam_names = app.enumerate(result.data.cam_names);
                app.vue.chosen_experiment_name = experiment_name;
                app.vue.cur_img_index = 0;
                app.update_button();
            });
    }

    app.get_timelapse = function (start, end) {
        if (app.vue.ready_to_get == false) {
            return;
        }
        app.vue.show_image_overlay = false;
        app.vue.loading = true;

        // TODO: Consider changing index_provided to the variable value
        axios.get(images_url, {params: {index_provided: false, make_timelapse: true, cur_img_index: start, experiment_name: app.vue.chosen_experiment_name, cam_name: app.vue.chosen_cam_name, page_size: end}})
        .then(function (result) {
            //app.vue.images = result.data.images;
            app.vue.timelapse_ready = true;
            //console.log(app.vue.images)
            app.vue.loading = false;
            app.vue.timelapse = result.data.timelapse;
            console.log("Timelapse loaded!")
            //app.vue.cur_img_index = parseInt(app.vue.cur_img_index) + parseInt(app.vue.page_size);
            //app.vue.file_names = result.data.file_names;
            // update the number in the text box for start index if it is outside of the range.
            // if (parseInt(result.data.total_image_count) <= parseInt(app.vue.start_index)+parseInt(app.vue.page_size)) {
            //     app.vue.start_index = result.data.total_image_count-app.vue.page_size;
            // }
            // app.vue.old_start_index = app.vue.start_index;
        });

    }

    app.get_images = function () {
        if (app.vue.ready_to_get == false) {
            return;
        }
        app.vue.show_image_overlay = false;
        app.vue.loading = true;
        // If the start index has never been provided before now, then set cur_img_index to the start index
        // if it has been provided before and has changed in the last call, then do the same, else, do nothing.
        if ((app.vue.old_start_index == null && app.vue.start_index != null) || (app.vue.start_index != app.vue.old_start_index && app.vue.start_index != null)) {
            app.vue.cur_img_index = app.vue.start_index;
        }
        if (app.vue.start_index != null) {
            app.vue.index_provided = true;
        }
        console.log("index_provided:", app.vue.index_provided);
        axios.get(images_url, {params: {make_timelapse: false, index_provided: app.vue.index_provided, start_index: app.vue.start_index, cur_img_index: app.vue.cur_img_index, experiment_name: app.vue.chosen_experiment_name, cam_name: app.vue.chosen_cam_name, page_size: app.vue.page_size}})
            .then(function (result) {
                app.vue.images = result.data.images;
                app.vue.images_ready = true;
                //console.log(app.vue.images)
                app.vue.loading = false;
                app.vue.cur_img_index = parseInt(app.vue.cur_img_index) + parseInt(app.vue.page_size);
                app.vue.file_names = result.data.file_names;
                // update the number in the text box for start index if it is outside of the range.
                if (parseInt(result.data.total_image_count) <= parseInt(app.vue.start_index)+parseInt(app.vue.page_size)) {
                    app.vue.start_index = result.data.total_image_count-app.vue.page_size;
                }
                app.vue.old_start_index = app.vue.start_index;
            });
    }

    app.set_camera = function (cam_name) {
        axios.get(set_camera_url, {params: {experiment_name: app.vue.chosen_experiment_name, cam_name: cam_name}})
            .then(function (result) {
                app.vue.chosen_cam_name = cam_name;
                app.vue.cur_img_index = 0;
                app.update_button();
            });
    }

    // This contains all the methods.
    app.methods = {
        // Complete as you see fit.
        get_experiments: app.get_experiments,
        get_images: app.get_images,
        set_camera: app.set_camera,
        set_experiment: app.set_experiment,
        get_timelapse: app.get_timelapse,
    };

    // This creates the Vue instance.
    app.vue = new Vue({
        el: "#vue-target",
        data: app.data,
        methods: app.methods
    });

    // And this initializes it.
    app.init = () => {
        axios.get(get_experiments_url).then(function (r) {
            if ('experiment_names' in r.data) {
                app.vue.experiment_names = app.enumerate(r.data.experiment_names);
            }
        })
        app.vue.images_ready = false
    };

    // Call to the initializer.
    app.init();
};

// This takes the (empty) app object, and initializes it,
// putting all the code i
init(app);