// components/SampleCodeVideo.js
const SampleCodeVideo = () => (
    <section className="bg-gray-900 text-white py-16">
        <div className="container mx-auto text-center">
            <h2 className="text-3xl font-semibold text-orange-300 mb-6">Sample Code Demonstration</h2>
            <iframe
                width="560"
                height="315"
                src="https://www.youtube.com/embed/sample_video_id"
                title="Sample Code Demonstration"
                frameBorder="0"
                allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
            ></iframe>
        </div>
    </section>
);

export default SampleCodeVideo;
