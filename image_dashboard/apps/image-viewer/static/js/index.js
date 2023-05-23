// This will be the object that will contain the Vue attributes
// and be used to initialize it.
let app = {};


// Given an empty app object, initializes it filling its attributes,
// creates a Vue instance, and then initializes the Vue instance.
let init = (app) => {

    // This is the Vue data.
    app.data = {
        query: "",
        meow: "",
        reply_meow: [],
        reply_mode: false,
        meow_id: 0,
        experiment_names: [],
        experiment_name: "",
        meows: [],
        user_rows: [],
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
    };

    app.enumerate = (a) => {
        // This adds an _idx field to each element of the array.
        let k = 0;
        a.map((e) => {e._idx = k++;});
        return a;
    };

    app.set_follow = function (user_id) {
        console.log("follow!")
        axios.get(set_follow_url, {params: {user_id: user_id}})
            .then(function (result) {
                axios.get(search_url).then(function (r) {
                    app.vue.user_rows = r.data.user_rows;
                })
            });
    }

    app.post_remeow = function (remeow) {
            axios.get(post_meow_url, {params: {m: remeow}})
                .then(function (result) {
                    axios.get(get_meows_url).then(function (r) {
                        app.vue.meows = app.enumerate(r.data.meows);
                    })
                });
    }

    app.post_meow = function () {
        if (app.vue.reply_mode) {
            app.post_reply(app.vue.meow)
        }
        else {
        axios.get(post_meow_url, {params: {m: app.vue.meow}})
            .then(function (result) {
                    
            });
        }
    }
    app.post_reply = function (reply) {
        axios.get(post_reply_url, {params: {reply: reply, meow_id: app.vue.meow_id}})
            .then(function (result) {
                    app.get_replies(app.vue.meow_id)
            });
    }

    app.get_replies = function (meow_id) {
        axios.get(get_replies_url, {params: {meow_id: meow_id}})
            .then(function (result) {
                for (let i = 0; i < app.vue.meows.length; i++) {
                    if (app.vue.meows[i].id == meow_id) {
                        app.vue.reply_meow = app.vue.meows[i];
                    }
                }
            
                app.vue.meows = app.enumerate(result.data.replies);
                app.vue.reply_mode = true;
                app.vue.meow_id = meow_id
            });
    }

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
            });
    }

    app.get_images = function (page_size) {
        if (!page_size) {
            page_size = app.vue.page_size;
        }
        else {
            app.vue.page_size = page_size;
        }
        app.vue.loading = true;
        axios.get(images_url, {params: {cur_img_index: app.vue.cur_img_index, experiment_name: app.vue.chosen_experiment_name, cam_name: app.vue.chosen_cam_name, page_size: page_size}})
            .then(function (result) {
                app.vue.images = result.data.images;
                app.vue.images_ready = true;
                //console.log(app.vue.images)
                app.vue.loading = false;
                app.vue.cur_img_index += app.vue.page_size;
                app.vue.file_names = result.data.file_names;
            });
    }

    app.set_camera = function (cam_name) {
        axios.get(set_camera_url, {params: {experiment_name: app.vue.chosen_experiment_name, cam_name: cam_name}})
            .then(function (result) {
                app.vue.chosen_cam_name = cam_name;
                app.vue.cur_img_index = 0;
            });
    }

    app.get_meows = function () {
        axios.get(get_meows_url)
            .then(function (result) {
                app.vue.meows = app.enumerate(result.data.meows);
                app.vue.reply_mode = false;
            });
    }

    app.your_meows = function () {
        axios.get(your_meows_url)
            .then(function (result) {
                app.vue.meows = app.enumerate(result.data.meows);
                app.vue.reply_mode = false;
            });
    }

    app.search = function () {
        console.log("searching!")
            axios.get(search_url, {params: {q: app.vue.query}})
                .then(function (result) {
                    app.vue.user_rows = result.data.user_rows;
                    if (result.length == 0) {
                        axios.get(search_url).then(function (r) {
                            app.vue.user_rows = r.data.user_rows;
                        })
                    }
                });
    }

    // This contains all the methods.
    app.methods = {
        // Complete as you see fit.
        post_meow: app.post_meow,
        post_reply: app.post_reply,
        get_experiments: app.get_experiments,
        your_meows: app.your_meows,
        post_remeow: app.post_remeow,
        get_images: app.get_images,
        search: app.search,
        set_camera: app.set_camera,
        set_experiment: app.set_experiment,
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
        // axios.get(search_url).then(function (r) {
        //     app.vue.user_rows = r.data.user_rows;
        //     console.log(app.vue.user_rows)
        //     console.log(search_url)
        // })
    };

    // Call to the initializer.
    app.init();
};

// This takes the (empty) app object, and initializes it,
// putting all the code i
init(app);