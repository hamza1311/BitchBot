import * as functions from 'firebase-functions';
import * as admin from 'firebase-admin';
const serviceAccount = require('../bitchbot-discordbot-firebase-adminsdk-hyo1e-bfd6127782.json');

admin.initializeApp({
    // credential: admin.credential.applicationDefault(),
    credential: admin.credential.cert(serviceAccount),
    databaseURL: "https://bitchbot-discordbot.firebaseio.com"
})


export const allEmojis = functions.https.onRequest(async (request, response) => {
    const data = await admin.firestore().collection('emoji').get()
    const list = data.docs
    const emojis = list.map(it => it.data())
    response.send(emojis)
})

export const saveUserInfo = functions.https.onRequest(async (request, response) => {
    const userInfo = request.body
    try {
        await admin.firestore().collection(`servers/${userInfo.serverId}/users`).doc(userInfo.id).set(userInfo)
        // await admin.firestore().collection('users').doc(userInfo.id).set(userInfo)
        response.send('OK')
    } catch (error) {
        response.send('error')
    }
})


export const getUserInfo = functions.https.onRequest(async (request, response) => {
    const userid = request.query.id
    const serverId = request.query.server_id

    try {
        const snapshot = await admin.firestore().collection(`servers/${serverId}/users`).doc(userid).get()
        // const snapshot = await admin.firestore().collection('users').doc(userid).get()
        const data = snapshot.data()
        response.send(data)
    } catch (error) {
        response.send(error)
    }
})

export const epicEmojis = functions.https.onRequest(async (request, response) => {
    const emojis = await admin.firestore().collection('epic_emojis').get()
    const list = emojis.docs.map(it => it.data())
    response.send(list)
})

export const roles = functions.https.onRequest(async (request, response) => {
    const serverId = request.query.id
    console.log(`serverId -> ${serverId}`)
    try {
        const snapshot = await admin.firestore().collection(`servers/${serverId}/roles`).get()
        const data = snapshot.docs.map(it => it.data())
        console.log(`data -> ${data}`)
        response.send(data)
    } catch (error) {
        console.log(error)
        response.send(error)
    }
})

export const getRoleIdForAssignment = functions.https.onRequest(async (request, response) => {
    const roleInfo = request.query
    try {
        const snapshot = await admin.firestore().collection(`servers/${roleInfo.server_id}/roles`).doc(roleInfo.role_name).get()
        const role = snapshot.data()
        response.send(role)
    } catch (error) {
        response.send(error)
    }
    
})

export const quotesChannels = functions.https.onRequest(async (request, response) => {
    try {
        const snapshot = await admin.firestore().collection(`/servers`).doc('quotesChannel').get()
        const data = snapshot.data()
        response.send(data)
    } catch (error) {
        console.error(error)
        response.send(error)
    }
})

export const setQuotesChannel = functions.https.onRequest(async (request, response) => {
    const body = request.body
    try {
        const snapshot = await admin.firestore().collection(`/servers`).doc('quotesChannel').get()
        const data = snapshot.data()
        if (data == undefined) { 
            response.send('data is undefined')
            return
        }
        data[body.guildId] = body.channelId


        await admin.firestore().collection(`/servers`).doc('quotesChannel').set(data)
        response.send('OK')
    } catch (error) {
        response.send('error')
    }
})
// BlameLucy

export const countersForServer = functions.https.onRequest(async (request, response) => {
    const serverId = request.query.serverId

    const snapshot = await admin.firestore().collection(`/servers/${serverId}/counters/`).get()
    const data = snapshot.docs.map(it => it.data())

    response.send(data)
})

export const updateCounter = functions.https.onRequest(async (request, response) => {
    const query = request.body
    const serverId = query.serverId
    const counter = query.counter
    const newValue = query.value

    await admin.firestore().collection(`/servers/${serverId}/counters/`).doc(counter).update({count: newValue})
    const snapshot = await admin.firestore().collection(`/servers/${serverId}/counters/`).doc(counter).get()
    const data = snapshot.data()

    response.send(data)
})
