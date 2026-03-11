const QUESTIONS = [
    {
        id: 1,
        category: "Landmarks",
        answer: "Eiffel Tower",
        acceptedAnswers: ["eiffel tower", "the eiffel tower", "la tour eiffel"],
        clues: [
            "I am one of the most recognizable structures in the world, attracting millions of visitors every year.",
            "I was originally built as a temporary exhibit and was once considered an eyesore by many locals.",
            "I was constructed in just over two years for the 1889 World's Fair.",
            "I am an iron lattice tower standing over 300 meters tall in the heart of a European capital city.",
            "I stand in Paris, France, and was designed by the engineer Gustave Eiffel."
        ]
    },
    {
        id: 2,
        category: "Science",
        answer: "Albert Einstein",
        acceptedAnswers: ["albert einstein", "einstein"],
        clues: [
            "I am considered one of the most influential thinkers in all of human history.",
            "My ideas changed how scientists — and the general public — understand the fundamental nature of reality.",
            "I fled my home country in the 1930s during a period of political turmoil and eventually settled in the United States.",
            "I am famous for the equation E=mc², which describes the relationship between energy and mass.",
            "I am the German-born physicist who developed the Theory of Relativity and won the Nobel Prize in Physics in 1921."
        ]
    },
    {
        id: 3,
        category: "Geography",
        answer: "Amazon River",
        acceptedAnswers: ["amazon river", "the amazon river", "amazon", "the amazon"],
        clues: [
            "I am considered one of the most vital natural features on our entire planet.",
            "My basin contains the largest tropical rainforest in the world and is home to an extraordinary diversity of life.",
            "I flow roughly from west to east, crossing an entire continent before reaching the ocean.",
            "I carry more water than any other river on Earth, accounting for about 20% of all river flow into the world's oceans.",
            "I am the great river that flows through South America — primarily through Brazil — and empties into the Atlantic Ocean."
        ]
    },
    {
        id: 4,
        category: "Literature",
        answer: "William Shakespeare",
        acceptedAnswers: ["william shakespeare", "shakespeare", "the bard"],
        clues: [
            "I am considered by many to be the greatest writer who ever lived.",
            "I worked in a form of entertainment that required actors, costumes, and stages.",
            "I was born in England in 1564 and died on April 23, 1616.",
            "I wrote 37 plays and 154 sonnets that are still performed and studied around the world today.",
            "I am the English playwright from Stratford-upon-Avon who wrote Romeo and Juliet, Hamlet, and Macbeth."
        ]
    },
    {
        id: 5,
        category: "Music",
        answer: "The Beatles",
        acceptedAnswers: ["the beatles", "beatles"],
        clues: [
            "This act is widely considered the most influential in the history of popular music.",
            "This group formed in the late 1950s in a working-class port city in England.",
            "They sparked 'Beatlemania' when they toured the United States for the first time in February 1964.",
            "Their members were John Lennon, Paul McCartney, George Harrison, and Ringo Starr.",
            "This British rock band from Liverpool released landmark albums including Abbey Road and Sgt. Pepper's Lonely Hearts Club Band."
        ]
    },
    {
        id: 6,
        category: "History",
        answer: "Great Wall of China",
        acceptedAnswers: ["great wall of china", "the great wall of china", "great wall", "the great wall"],
        clues: [
            "This is one of the greatest architectural achievements in all of human history.",
            "It was built over many centuries to defend a great empire from nomadic invasions from the north.",
            "Different sections were constructed by different dynasties starting as early as the 7th century BC.",
            "It stretches across mountains, deserts, and plains for thousands of kilometers.",
            "This massive fortification runs along the northern borders of China and is one of the most visited tourist sites in the world."
        ]
    },
    {
        id: 7,
        category: "Technology",
        answer: "The Internet",
        acceptedAnswers: ["the internet", "internet"],
        clues: [
            "This invention has transformed modern society more profoundly than almost anything else in recent history.",
            "It was originally developed in the 1960s for military and academic research communications.",
            "Its early predecessor, ARPANET, first connected computers at just four American universities in 1969.",
            "Tim Berners-Lee created the World Wide Web in 1989, making this technology accessible to everyone.",
            "This global system of interconnected computer networks now connects billions of people and devices worldwide."
        ]
    },
    {
        id: 8,
        category: "Geography",
        answer: "Mount Everest",
        acceptedAnswers: ["mount everest", "everest", "mt everest", "mt. everest"],
        clues: [
            "This is considered one of the greatest physical challenges and achievements in human endurance.",
            "It sits on the border between two Asian countries within the world's largest mountain range.",
            "Sir Edmund Hillary and Tenzing Norgay became the first confirmed people to reach its summit in May 1953.",
            "It stands at 8,849 meters (29,032 feet) above sea level.",
            "This peak in the Himalayas, on the border between Nepal and Tibet, is the highest point on Earth."
        ]
    },
    {
        id: 9,
        category: "Art",
        answer: "Mona Lisa",
        acceptedAnswers: ["mona lisa", "the mona lisa", "la gioconda"],
        clues: [
            "This is the most visited and most written-about artwork in the world.",
            "It was created during the Italian Renaissance, a period of extraordinary artistic achievement.",
            "It was stolen from a famous Paris museum in 1911 and was missing for two years before being recovered.",
            "It depicts a woman with an enigmatic smile sitting before a distant, hazy landscape.",
            "This portrait was painted by Leonardo da Vinci between approximately 1503 and 1519 and now hangs in the Louvre."
        ]
    },
    {
        id: 10,
        category: "Space",
        answer: "The Moon",
        acceptedAnswers: ["the moon", "moon", "luna"],
        clues: [
            "Humans have gazed at this celestial body with wonder and curiosity throughout all of recorded history.",
            "It influences life on Earth in measurable ways, including the daily tides of our oceans.",
            "It is the fifth largest natural satellite in our solar system.",
            "Twelve humans have walked on its surface, the last doing so in December 1972.",
            "This is Earth's only natural satellite, and Neil Armstrong was the first person to set foot on it in 1969."
        ]
    }
];
